"""Unit tests for LoRA models listing."""
def test_lora_models():
    models = [{'name': 'lora1', 'type': 'lora'}]
    assert models[0]['type'] == 'lora'
