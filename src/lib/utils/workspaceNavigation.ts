type WorkspacePermissions = {
	models?: boolean;
	knowledge?: boolean;
	prompts?: boolean;
	tools?: boolean;
	skills?: boolean;
};

type WorkspaceUser = {
	role?: string | null;
	permissions?: {
		workspace?: WorkspacePermissions | null;
	} | null;
} | null | undefined;

const hasWorkspaceAccess = (
	currentUser: WorkspaceUser,
	section: keyof WorkspacePermissions
) => {
	return currentUser?.role === 'admin' || Boolean(currentUser?.permissions?.workspace?.[section]);
};

export const shouldShowKnowledgeEntry = (currentUser: WorkspaceUser) => {
	return hasWorkspaceAccess(currentUser, 'knowledge');
};

export const getWorkspaceLandingPath = (currentUser: WorkspaceUser) => {
	if (hasWorkspaceAccess(currentUser, 'knowledge')) {
		return '/workspace/knowledge';
	}

	if (hasWorkspaceAccess(currentUser, 'models')) {
		return '/workspace/models';
	}

	if (hasWorkspaceAccess(currentUser, 'prompts')) {
		return '/workspace/prompts';
	}

	if (hasWorkspaceAccess(currentUser, 'tools')) {
		return '/workspace/tools';
	}

	if (hasWorkspaceAccess(currentUser, 'skills')) {
		return '/workspace/skills';
	}

	return '/';
};
