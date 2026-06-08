import { afterEach, describe, expect, it, vi } from 'vitest';

import {
  MAX_PROMPT_IMAGE_DIMENSION,
  promptImageTargetDimensions,
  readPromptImageFiles,
} from '../workspace-prompt-images';

let fakeImageWidth = 1;
let fakeImageHeight = 1;

class FakeImage {
  onload: (() => void) | null = null;
  onerror: (() => void) | null = null;
  naturalWidth = fakeImageWidth;
  naturalHeight = fakeImageHeight;
  width = fakeImageWidth;
  height = fakeImageHeight;

  set src(_value: string) {
    this.naturalWidth = fakeImageWidth;
    this.naturalHeight = fakeImageHeight;
    this.width = fakeImageWidth;
    this.height = fakeImageHeight;
    queueMicrotask(() => this.onload?.());
  }
}

const installImageMock = (width: number, height: number): void => {
  fakeImageWidth = width;
  fakeImageHeight = height;
  vi.stubGlobal('Image', FakeImage);
};

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe('promptImageTargetDimensions', () => {
  it('keeps images inside the max dimension unchanged', () => {
    expect(promptImageTargetDimensions(1024, 768)).toEqual({
      width: 1024,
      height: 768,
      resized: false,
    });
  });

  it('scales oversized images to fit the Codex prompt image cap', () => {
    expect(promptImageTargetDimensions(4096, 2048)).toEqual({
      width: MAX_PROMPT_IMAGE_DIMENSION,
      height: 1024,
      resized: true,
    });
    expect(promptImageTargetDimensions(1024, 4096)).toEqual({
      width: 512,
      height: MAX_PROMPT_IMAGE_DIMENSION,
      resized: true,
    });
  });
});

describe('readPromptImageFiles', () => {
  it('preserves an in-bounds PNG data URL without canvas re-encoding', async () => {
    installImageMock(640, 480);
    const getContext = vi.spyOn(HTMLCanvasElement.prototype, 'getContext');
    const file = new File([new Uint8Array([1, 2, 3])], 'small.png', { type: 'image/png' });

    const [image] = await readPromptImageFiles([file]);

    expect(image.mimeType).toBe('image/png');
    expect(image.imageUrl).toBe('data:image/png;base64,AQID');
    expect(getContext).not.toHaveBeenCalled();
  });

  it('downscales an oversized pasted image before creating the wire data URL', async () => {
    installImageMock(4096, 2048);
    const drawImage = vi.fn();
    vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue({ drawImage } as never);
    vi.spyOn(HTMLCanvasElement.prototype, 'toBlob').mockImplementation(function toBlob(callback, type) {
      expect(this.width).toBe(MAX_PROMPT_IMAGE_DIMENSION);
      expect(this.height).toBe(1024);
      callback(new Blob(['resized'], { type: String(type || 'image/png') }));
    });
    const file = new File([new Uint8Array([1, 2, 3])], 'large.png', { type: 'image/png' });

    const [image] = await readPromptImageFiles([file]);

    expect(drawImage).toHaveBeenCalled();
    expect(image.mimeType).toBe('image/png');
    expect(image.imageUrl).toBe('data:image/png;base64,cmVzaXplZA==');
  });
});
