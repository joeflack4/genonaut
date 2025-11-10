"""ComfyUI workflow builder service."""

import uuid
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from genonaut.api.exceptions import ValidationError


@dataclass
class LoRAModel:
    """LoRA model configuration."""
    name: str
    strength_model: float = 0.8
    strength_clip: float = 0.8


@dataclass
class SamplerParams:
    """KSampler parameters configuration."""
    seed: int = 123456
    steps: int = 28
    cfg: float = 5.5
    sampler_name: str = "euler"
    scheduler: str = "normal"
    denoise: float = 1.0


@dataclass
class GenerationRequest:
    """ComfyUI generation request parameters."""
    prompt: str
    checkpoint_model: str
    negative_prompt: str = ""
    lora_models: List[LoRAModel] = None
    width: int = 832
    height: int = 1216
    batch_size: int = 1
    sampler_params: SamplerParams = None
    filename_prefix: str = "genonaut_gen"

    def __post_init__(self):
        if self.lora_models is None:
            self.lora_models = []
        if self.sampler_params is None:
            self.sampler_params = SamplerParams()


class WorkflowBuilder:
    """Builder for ComfyUI workflows from generation requests."""

    def __init__(self):
        """Initialize workflow builder."""
        pass

    def validate_request(self, request: GenerationRequest) -> None:
        """Validate generation request parameters.

        Args:
            request: Generation request to validate

        Raises:
            ValidationError: If request parameters are invalid
        """
        if not request.prompt or not request.prompt.strip():
            raise ValidationError("Prompt cannot be empty")

        if not request.checkpoint_model:
            raise ValidationError("Checkpoint model must be specified")

        if request.width <= 0 or request.height <= 0:
            raise ValidationError("Width and height must be positive")

        if request.batch_size <= 0 or request.batch_size > 10:
            raise ValidationError("Batch size must be between 1 and 10")

        if request.sampler_params.steps <= 0 or request.sampler_params.steps > 100:
            raise ValidationError("Steps must be between 1 and 100")

        if request.sampler_params.cfg < 0 or request.sampler_params.cfg > 20:
            raise ValidationError("CFG must be between 0 and 20")

        for lora in request.lora_models:
            if lora.strength_model < 0 or lora.strength_model > 3:
                raise ValidationError(
                    f"LoRA model strength must be between 0 and 3, got {lora.strength_model}"
                )
            if lora.strength_clip < 0 or lora.strength_clip > 3:
                raise ValidationError(
                    f"LoRA clip strength must be between 0 and 3, got {lora.strength_clip}"
                )

    def build_workflow(self, request: GenerationRequest, client_id: Optional[str] = None) -> Dict[str, Any]:
        """Build ComfyUI workflow from generation request.

        Args:
            request: Generation request parameters
            client_id: Optional client ID for tracking

        Returns:
            ComfyUI workflow dictionary

        Raises:
            ValidationError: If request parameters are invalid
        """
        self.validate_request(request)

        if not client_id:
            client_id = str(uuid.uuid4())

        # Node counter for generating unique node IDs
        node_id = 1

        # Build workflow nodes - return just the prompt nodes
        nodes = {}

        # 1. CheckpointLoaderSimple - Load base model
        checkpoint_node_id = str(node_id)
        nodes[checkpoint_node_id] = {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": request.checkpoint_model}
        }
        node_id += 1

        # Track the current model and clip outputs for chaining LoRA models
        current_model_output = [checkpoint_node_id, 0]
        current_clip_output = [checkpoint_node_id, 1]
        current_vae_output = [checkpoint_node_id, 2]

        # 2. LoraLoader nodes - Apply LoRA models in sequence
        for lora in request.lora_models:
            lora_node_id = str(node_id)
            nodes[lora_node_id] = {
                "class_type": "LoraLoader",
                "inputs": {
                    "model": current_model_output,
                    "clip": current_clip_output,
                    "lora_name": lora.name,
                    "strength_model": lora.strength_model,
                    "strength_clip": lora.strength_clip
                }
            }
            # Update outputs for next LoRA or subsequent nodes
            current_model_output = [lora_node_id, 0]
            current_clip_output = [lora_node_id, 1]
            node_id += 1

        # 3. CLIPTextEncode - Positive prompt
        positive_prompt_node_id = str(node_id)
        nodes[positive_prompt_node_id] = {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "clip": current_clip_output,
                "text": request.prompt
            }
        }
        node_id += 1

        # 4. CLIPTextEncode - Negative prompt
        negative_prompt_node_id = str(node_id)
        nodes[negative_prompt_node_id] = {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "clip": current_clip_output,
                "text": request.negative_prompt
            }
        }
        node_id += 1

        # 5. EmptyLatentImage - Define image dimensions
        latent_node_id = str(node_id)
        nodes[latent_node_id] = {
            "class_type": "EmptyLatentImage",
            "inputs": {
                "width": request.width,
                "height": request.height,
                "batch_size": request.batch_size
            }
        }
        node_id += 1

        # 6. KSampler - Perform generation
        sampler_node_id = str(node_id)
        nodes[sampler_node_id] = {
            "class_type": "KSampler",
            "inputs": {
                "seed": request.sampler_params.seed,
                "steps": request.sampler_params.steps,
                "cfg": request.sampler_params.cfg,
                "sampler_name": request.sampler_params.sampler_name,
                "scheduler": request.sampler_params.scheduler,
                "denoise": request.sampler_params.denoise,
                "model": current_model_output,
                "positive": [positive_prompt_node_id, 0],
                "negative": [negative_prompt_node_id, 0],
                "latent_image": [latent_node_id, 0]
            }
        }
        node_id += 1

        # 7. VAEDecode - Decode latent to image
        vae_decode_node_id = str(node_id)
        nodes[vae_decode_node_id] = {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": [sampler_node_id, 0],
                "vae": current_vae_output
            }
        }
        node_id += 1

        # 8. SaveImage - Save generated image
        save_node_id = str(node_id)
        nodes[save_node_id] = {
            "class_type": "SaveImage",
            "inputs": {
                "images": [vae_decode_node_id, 0],
                "filename_prefix": request.filename_prefix
            }
        }

        return nodes

    def build_workflow_from_dict(self, params: Dict[str, Any], client_id: Optional[str] = None) -> Dict[str, Any]:
        """Build workflow from dictionary parameters.

        Args:
            params: Dictionary containing generation parameters
            client_id: Optional client ID for tracking

        Returns:
            ComfyUI workflow dictionary
        """
        # Convert LoRA models from dict format
        lora_models = []
        if "lora_models" in params and params["lora_models"]:
            for lora_dict in params["lora_models"]:
                lora_models.append(LoRAModel(
                    name=lora_dict["name"],
                    strength_model=lora_dict.get("strength_model", 0.8),
                    strength_clip=lora_dict.get("strength_clip", 0.8)
                ))

        # Convert sampler parameters
        sampler_params = SamplerParams()
        if "sampler_params" in params and params["sampler_params"]:
            sp = params["sampler_params"]
            sampler_params = SamplerParams(
                seed=sp.get("seed", 123456),
                steps=sp.get("steps", 28),
                cfg=sp.get("cfg", 5.5),
                sampler_name=sp.get("sampler_name", "euler"),
                scheduler=sp.get("scheduler", "normal"),
                denoise=sp.get("denoise", 1.0)
            )

        # Build request object
        request = GenerationRequest(
            prompt=params["prompt"],
            negative_prompt=params.get("negative_prompt", ""),
            checkpoint_model=params["checkpoint_model"],
            lora_models=lora_models,
            width=params.get("width", 832),
            height=params.get("height", 1216),
            batch_size=params.get("batch_size", 1),
            sampler_params=sampler_params,
            filename_prefix=params.get("filename_prefix", "genonaut_gen")
        )

        return self.build_workflow(request, client_id)

    def get_workflow_summary(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Extract summary information from a workflow.

        Args:
            workflow: ComfyUI workflow dictionary

        Returns:
            Dictionary with workflow summary information
        """
        nodes = workflow.get("prompt", {})
        summary = {
            "node_count": len(nodes),
            "checkpoint_model": None,
            "lora_models": [],
            "prompt": None,
            "negative_prompt": None,
            "dimensions": None,
            "sampler_settings": None
        }

        for node_id, node in nodes.items():
            class_type = node.get("class_type")
            inputs = node.get("inputs", {})

            if class_type == "CheckpointLoaderSimple":
                summary["checkpoint_model"] = inputs.get("ckpt_name")

            elif class_type == "LoraLoader":
                summary["lora_models"].append({
                    "name": inputs.get("lora_name"),
                    "strength_model": inputs.get("strength_model"),
                    "strength_clip": inputs.get("strength_clip")
                })

            elif class_type == "CLIPTextEncode":
                text = inputs.get("text", "")
                if not summary["prompt"]:
                    summary["prompt"] = text
                elif text != summary["prompt"]:
                    summary["negative_prompt"] = text

            elif class_type == "EmptyLatentImage":
                summary["dimensions"] = {
                    "width": inputs.get("width"),
                    "height": inputs.get("height"),
                    "batch_size": inputs.get("batch_size")
                }

            elif class_type == "KSampler":
                summary["sampler_settings"] = {
                    "seed": inputs.get("seed"),
                    "steps": inputs.get("steps"),
                    "cfg": inputs.get("cfg"),
                    "sampler_name": inputs.get("sampler_name"),
                    "scheduler": inputs.get("scheduler"),
                    "denoise": inputs.get("denoise")
                }

        return summary
