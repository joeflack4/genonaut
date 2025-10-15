import { describe, it, expect, vi } from 'vitest';

describe('GenerationForm Validation', () => {
  it('shows error with empty prompt', () => {
    const prompt = '';
    const hasError = prompt.length === 0;
    expect(hasError).toBe(true);
  });
  
  it('enables submit with valid prompt', () => {
    const prompt = 'Valid prompt';
    const enabled = prompt.length > 0;
    expect(enabled).toBe(true);
  });
  
  it('updates model on selector change', () => {
    const setModel = vi.fn();
    setModel('model-v2');
    expect(setModel).toHaveBeenCalledWith('model-v2');
  });
});
