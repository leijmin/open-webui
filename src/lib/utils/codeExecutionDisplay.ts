type DetailAttributes = {
	type?: string | null;
} | null | undefined;

type CodeExecutionOutput = {
	collapsed: boolean;
	attributes?: DetailAttributes;
	executing?: boolean | null;
	stdout?: unknown;
	stderr?: unknown;
	result?: unknown;
	files?: unknown;
};

const isCodeInterpreter = (attributes?: DetailAttributes) => {
	return attributes?.type === 'code_interpreter';
};

const hasDisplayValue = (value: unknown) => {
	if (value === null || value === undefined) {
		return false;
	}

	if (typeof value === 'string') {
		return value.length > 0;
	}

	if (Array.isArray(value)) {
		return value.length > 0;
	}

	return true;
};

export const shouldAutoExpandCodeInterpreterDetails = (
	expandDetails: boolean,
	attributes?: DetailAttributes
) => {
	return isCodeInterpreter(attributes) || expandDetails;
};

export const shouldCollapseCodeBlockByDefault = (
	collapseCodeBlocks: boolean,
	attributes?: DetailAttributes
) => {
	return isCodeInterpreter(attributes) ? false : collapseCodeBlocks;
};

export const shouldShowCodeExecutionOutput = ({
	collapsed,
	attributes,
	executing,
	stdout,
	stderr,
	result,
	files
}: CodeExecutionOutput) => {
	const hasOutput =
		Boolean(executing) ||
		hasDisplayValue(stdout) ||
		hasDisplayValue(stderr) ||
		hasDisplayValue(result) ||
		hasDisplayValue(files);

	if (!hasOutput) {
		return false;
	}

	return !collapsed || isCodeInterpreter(attributes);
};

export const formatCodeExecutionResult = (result: unknown) => {
	if (result === null || result === undefined) {
		return '';
	}

	if (typeof result === 'string') {
		return result;
	}

	return JSON.stringify(result, null, 2);
};
