type WebSearchSettings = {
	webSearch?: string | null;
};

const hasOwnProperty = (value: unknown, key: string) =>
	typeof value === 'object' &&
	value !== null &&
	Object.prototype.hasOwnProperty.call(value, key);

export const getWebSearchMode = (settings?: WebSearchSettings | null) => {
	if (!hasOwnProperty(settings, 'webSearch')) {
		return 'always';
	}

	return settings?.webSearch ?? null;
};
