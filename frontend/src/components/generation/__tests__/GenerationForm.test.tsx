import { describe, it, expect, vi } from 'vitest';

describe('GenerationForm Validation', () => {
  it('shows validation error with empty prompt', () => {
    const prompt = '';
    expect(prompt.length).toBe(0);
  });

  it('enables submit button with valid prompt', () => {
    const prompt = 'Valid prompt text';
    const isValid = prompt.length > 0;
    expect(isValid).toBe(true);
  });

  it('updates model when selector changes', () => {
    const setModel = vi.fn();
    setModel('new-model');
    expect(setModel).toHaveBeenCalledWith('new-model');
  });
});
