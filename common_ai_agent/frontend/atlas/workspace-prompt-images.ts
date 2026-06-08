export type PromptImageAttachment = {
  readonly id: string;
  readonly name: string;
  readonly mimeType: string;
  readonly imageUrl: string;
};

export type PromptImageWireAttachment = {
  readonly image_url: string;
  readonly detail: 'auto' | 'low' | 'high';
};

export type PromptSubmitPayload = {
  readonly text: string;
  readonly images: readonly PromptImageAttachment[];
};

export type PromptSubmitCommand =
  | string
  | {
    readonly text?: string;
    readonly images?: readonly PromptImageAttachment[];
  };

export const MAX_PROMPT_IMAGE_DIMENSION = 2048;

const RESIZED_IMAGE_QUALITY = 0.85;
const PRESERVABLE_IMAGE_TYPES = new Set(['image/jpeg', 'image/png', 'image/webp']);

const fallbackImageName = (index: number, mimeType: string): string => {
  const ext = mimeType === 'image/jpeg' ? 'jpg'
    : mimeType === 'image/gif' ? 'gif'
      : mimeType === 'image/webp' ? 'webp'
        : 'png';
  return `clipboard-${index + 1}.${ext}`;
};

const imageId = (): string => {
  const cryptoApi = globalThis.crypto;
  if (cryptoApi && typeof cryptoApi.randomUUID === 'function') {
    return cryptoApi.randomUUID();
  }
  return `img-${Date.now()}-${Math.random().toString(16).slice(2)}`;
};

export const promptImageTargetDimensions = (
  width: number,
  height: number,
  maxDimension: number = MAX_PROMPT_IMAGE_DIMENSION,
): { width: number; height: number; resized: boolean } => {
  if (!Number.isFinite(width) || !Number.isFinite(height) || width <= 0 || height <= 0) {
    return { width: 0, height: 0, resized: false };
  }
  if (width <= maxDimension && height <= maxDimension) {
    return { width: Math.round(width), height: Math.round(height), resized: false };
  }
  const scale = maxDimension / Math.max(width, height);
  return {
    width: Math.max(1, Math.round(width * scale)),
    height: Math.max(1, Math.round(height * scale)),
    resized: true,
  };
};

const readFileAsDataUrl = (file: Blob): Promise<string> =>
  new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = () => {
      reject(reader.error ?? new Error('Unable to read pasted image'));
    };
    reader.onload = () => {
      const result = reader.result;
      if (typeof result !== 'string') {
        reject(new Error('Pasted image did not produce a data URL'));
        return;
      }
      resolve(result);
    };
    reader.readAsDataURL(file);
  });

const loadImageElement = (imageUrl: string): Promise<HTMLImageElement> =>
  new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = () => resolve(image);
    image.onerror = () => reject(new Error('Unable to decode pasted image'));
    image.src = imageUrl;
  });

const canvasToBlob = (
  canvas: HTMLCanvasElement,
  mimeType: string,
  quality?: number,
): Promise<Blob> =>
  new Promise((resolve, reject) => {
    canvas.toBlob((blob) => {
      if (!blob) {
        reject(new Error('Unable to encode pasted image'));
        return;
      }
      resolve(blob);
    }, mimeType, quality);
  });

const normalizeCanvasMimeType = (mimeType: string): string =>
  mimeType === 'image/jpeg' || mimeType === 'image/webp' ? mimeType : 'image/png';

const resizePromptImageDataUrl = async (
  sourceDataUrl: string,
  mimeType: string,
): Promise<{ imageUrl: string; mimeType: string }> => {
  const image = await loadImageElement(sourceDataUrl);
  const target = promptImageTargetDimensions(
    image.naturalWidth || image.width,
    image.naturalHeight || image.height,
  );
  if (!target.resized && PRESERVABLE_IMAGE_TYPES.has(mimeType)) {
    return { imageUrl: sourceDataUrl, mimeType };
  }

  const canvas = document.createElement('canvas');
  canvas.width = target.width;
  canvas.height = target.height;
  const context = canvas.getContext('2d');
  if (!context) {
    throw new Error('Unable to prepare pasted image for upload');
  }
  context.drawImage(image, 0, 0, target.width, target.height);

  const outputMimeType = normalizeCanvasMimeType(mimeType);
  const blob = await canvasToBlob(canvas, outputMimeType, RESIZED_IMAGE_QUALITY);
  return {
    imageUrl: await readFileAsDataUrl(blob),
    mimeType: blob.type || outputMimeType,
  };
};

const readPromptImageFile = (file: File, index: number): Promise<PromptImageAttachment> =>
  readFileAsDataUrl(file).then(async (sourceDataUrl) => {
    const sourceMimeType = file.type || 'image/png';
    const processed = await resizePromptImageDataUrl(sourceDataUrl, sourceMimeType);
    return {
      id: imageId(),
      name: file.name || fallbackImageName(index, processed.mimeType),
      mimeType: processed.mimeType,
      imageUrl: processed.imageUrl,
    };
  });

export const promptImageFilesFromClipboard = (clipboardData: DataTransfer | null): readonly File[] => {
  if (!clipboardData) return [];
  const files: File[] = [];
  for (const item of Array.from(clipboardData.items || [])) {
    if (item.kind !== 'file' || !item.type.startsWith('image/')) continue;
    const file = item.getAsFile();
    if (file) files.push(file);
  }
  if (files.length) return files;
  for (const file of Array.from(clipboardData.files || [])) {
    if (file.type.startsWith('image/')) files.push(file);
  }
  return files;
};

export const readPromptImageFiles = async (
  files: readonly File[],
): Promise<readonly PromptImageAttachment[]> => Promise.all(files.map(readPromptImageFile));

export const normalizePromptSubmit = (
  cmd: PromptSubmitCommand | undefined,
  fallbackText: string,
  fallbackImages: readonly PromptImageAttachment[],
): PromptSubmitPayload => {
  if (typeof cmd === 'string' || cmd === undefined) {
    return { text: String(cmd ?? fallbackText).trim(), images: fallbackImages };
  }
  return {
    text: String(cmd.text ?? fallbackText).trim(),
    images: cmd.images ?? fallbackImages,
  };
};

export const promptFeedText = (
  text: string,
  images: readonly PromptImageAttachment[],
): string => {
  if (text) return text;
  return images.length ? `[Image ${images.length}]` : '';
};

export const toPromptWireImages = (
  images: readonly PromptImageAttachment[],
): readonly PromptImageWireAttachment[] => images.map((image) => ({
  image_url: image.imageUrl,
  detail: 'high',
}));
