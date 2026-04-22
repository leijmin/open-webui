import { describe, expect, test } from 'vitest';

import {
	getWorkspaceLandingPath,
	shouldShowKnowledgeEntry
} from './workspaceNavigation';

describe('workspace navigation rules', () => {
	test('admins land on knowledge by default', () => {
		expect(
			getWorkspaceLandingPath({
				role: 'admin',
				permissions: {
					workspace: {
						models: true,
						knowledge: true,
						prompts: true,
						tools: true,
						skills: true
					}
				}
			})
		).toBe('/workspace/knowledge');
	});

	test('knowledge users land on knowledge by default', () => {
		expect(
			getWorkspaceLandingPath({
				role: 'user',
				permissions: {
					workspace: {
						knowledge: true
					}
				}
			})
		).toBe('/workspace/knowledge');
	});

	test('users without knowledge fall back to the first allowed technical area', () => {
		expect(
			getWorkspaceLandingPath({
				role: 'user',
				permissions: {
					workspace: {
						models: true,
						prompts: true
					}
				}
			})
		).toBe('/workspace/models');
	});

	test('knowledge entry stays visible only for admins or knowledge-enabled users', () => {
		expect(
			shouldShowKnowledgeEntry({
				role: 'admin',
				permissions: {
					workspace: {}
				}
			})
		).toBe(true);

		expect(
			shouldShowKnowledgeEntry({
				role: 'user',
				permissions: {
					workspace: {
						knowledge: true
					}
				}
			})
		).toBe(true);

		expect(
			shouldShowKnowledgeEntry({
				role: 'user',
				permissions: {
					workspace: {
						models: true
					}
				}
			})
		).toBe(false);
	});
});
