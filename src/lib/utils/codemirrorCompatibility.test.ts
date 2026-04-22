import { describe, expect, test } from 'vitest';

import { basicSetup } from 'codemirror';
import { EditorState } from '@codemirror/state';
import { keymap } from '@codemirror/view';

describe('codemirror compatibility', () => {
	test('basicSetup works with direct @codemirror extensions', () => {
		expect(() =>
			EditorState.create({
				doc: 'print("胡椒文旅")',
				extensions: [basicSetup, keymap.of([])]
			})
		).not.toThrow();
	});
});
