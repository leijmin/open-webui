type LoaderVisibilityState = {
	isVisible: boolean;
	shouldDispatch: boolean;
};

export const getLoaderVisibilityState = (
	isVisible: boolean,
	isIntersecting: boolean
): LoaderVisibilityState => {
	if (isIntersecting) {
		return {
			isVisible: true,
			shouldDispatch: !isVisible
		};
	}

	return {
		isVisible: false,
		shouldDispatch: false
	};
};
