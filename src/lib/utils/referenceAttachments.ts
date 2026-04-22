export type ReferenceSource = 'knowledge' | 'note';

export type ReferenceAttachment = Record<string, unknown> & {
	id?: string | number;
	type?: string;
	referenceSource?: ReferenceSource;
	status?: string;
};

const getReferenceKey = (item: ReferenceAttachment, source: ReferenceSource) => {
	return `${source}:${item?.type ?? ''}:${item?.id ?? ''}`;
};

const isSameReferenceItem = (
	item: ReferenceAttachment,
	target: ReferenceAttachment,
	source: ReferenceSource
) => {
	return (
		item?.referenceSource === source &&
		getReferenceKey(item, source) === getReferenceKey(target, source)
	);
};

export const countReferenceAttachments = (
	files: ReferenceAttachment[],
	source: ReferenceSource
) => {
	return files.filter((item) => item?.referenceSource === source).length;
};

export const clearReferenceAttachments = (
	files: ReferenceAttachment[],
	source: ReferenceSource
) => {
	return files.filter((item) => item?.referenceSource !== source);
};

export const isReferenceAttachmentSelected = (
	files: ReferenceAttachment[],
	item: ReferenceAttachment,
	source: ReferenceSource
) => {
	return files.some((file) => isSameReferenceItem(file, item, source));
};

export const toggleReferenceAttachment = (
	files: ReferenceAttachment[],
	item: ReferenceAttachment,
	source: ReferenceSource
) => {
	const exists = files.some((file) => isSameReferenceItem(file, item, source));

	if (exists) {
		return files.filter((file) => !isSameReferenceItem(file, item, source));
	}

	return [
		...files,
		{
			...item,
			status: item?.status ?? 'processed',
			referenceSource: source
		}
	];
};

export const replaceReferenceAttachments = (
	files: ReferenceAttachment[],
	items: ReferenceAttachment[],
	source: ReferenceSource
) => {
	const nextFiles = clearReferenceAttachments(files, source);
	const seen = new Set<string>();

	const normalizedItems = items.reduce<ReferenceAttachment[]>((acc, item) => {
		const key = getReferenceKey(item, source);
		if (seen.has(key)) {
			return acc;
		}

		seen.add(key);
		acc.push({
			...item,
			status: item?.status ?? 'processed',
			referenceSource: source
		});

		return acc;
	}, []);

	return [...nextFiles, ...normalizedItems];
};

export const getVisibleComposerFiles = (files: ReferenceAttachment[]) => {
	return files.filter((item) => !item?.referenceSource);
};

export const areReferenceAttachmentsFullySelected = (
	files: ReferenceAttachment[],
	items: ReferenceAttachment[],
	source: ReferenceSource
) => {
	if (items.length === 0) {
		return false;
	}

	return items.every((item) => isReferenceAttachmentSelected(files, item, source));
};
