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

const readPromptImageFile = (file: File, index: number): Promise<PromptImageAttachment> =>
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
      const mimeType = file.type || 'image/png';
      resolve({
        id: imageId(),
        name: file.name || fallbackImageName(index, mimeType),
        mimeType,
        imageUrl: result,
      });
    };
    reader.readAsDataURL(file);
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
