import { describe, expect, test } from 'vitest';

import {
	areReferenceAttachmentsFullySelected,
	clearReferenceAttachments,
	countReferenceAttachments,
	getVisibleComposerFiles,
	isReferenceAttachmentSelected,
	replaceReferenceAttachments,
	type ReferenceAttachment,
	toggleReferenceAttachment
} from './referenceAttachments';

describe('reference attachment helpers', () => {
	test('toggle adds and removes a source-scoped reference item', () => {
		const files = toggleReferenceAttachment([], { id: 'kb-1', type: 'collection' }, 'knowledge');

		expect(files).toEqual([
			{
				id: 'kb-1',
				type: 'collection',
				status: 'processed',
				referenceSource: 'knowledge'
			}
		]);

		expect(
			toggleReferenceAttachment(files, { id: 'kb-1', type: 'collection' }, 'knowledge')
		).toEqual([]);
	});

	test('toggle does not treat non-reference attachments as existing references', () => {
		expect(
			toggleReferenceAttachment(
				[{ id: 'kb-1', type: 'collection' }],
				{ id: 'kb-1', type: 'collection' },
				'knowledge'
			)
		).toEqual([
			{ id: 'kb-1', type: 'collection' },
			{
				id: 'kb-1',
				type: 'collection',
				status: 'processed',
				referenceSource: 'knowledge'
			}
		]);
	});

	test('replace updates one source without touching unrelated attachments', () => {
		expect(
			replaceReferenceAttachments(
				[
					{ id: 'upload-1', type: 'doc' },
					{ id: 'old-kb', type: 'collection', referenceSource: 'knowledge' },
					{ id: 'note-1', type: 'note', referenceSource: 'note' }
				],
				[
					{ id: 'kb-1', type: 'collection' },
					{ id: 'kb-2', type: 'collection' }
				],
				'knowledge'
			)
		).toEqual([
			{ id: 'upload-1', type: 'doc' },
			{ id: 'note-1', type: 'note', referenceSource: 'note' },
			{ id: 'kb-1', type: 'collection', status: 'processed', referenceSource: 'knowledge' },
			{ id: 'kb-2', type: 'collection', status: 'processed', referenceSource: 'knowledge' }
		]);
	});

	test('clear removes only the selected reference source', () => {
		expect(
			clearReferenceAttachments(
				[
					{ id: 'kb-1', type: 'collection', referenceSource: 'knowledge' },
					{ id: 'note-1', type: 'note', referenceSource: 'note' },
					{ id: 'upload-1', type: 'doc' }
				],
				'knowledge'
			)
		).toEqual([
			{ id: 'note-1', type: 'note', referenceSource: 'note' },
			{ id: 'upload-1', type: 'doc' }
		]);
	});

	test('counts and visible files ignore hidden reference chips correctly', () => {
		const files: ReferenceAttachment[] = [
			{ id: 'kb-1', type: 'collection', referenceSource: 'knowledge' },
			{ id: 'note-1', type: 'note', referenceSource: 'note' },
			{ id: 'upload-1', type: 'doc' }
		];

		expect(countReferenceAttachments(files, 'knowledge')).toBe(1);
		expect(countReferenceAttachments(files, 'note')).toBe(1);
		expect(getVisibleComposerFiles(files)).toEqual([{ id: 'upload-1', type: 'doc' }]);
	});

	test('selected state matches only the same source item', () => {
		const files: ReferenceAttachment[] = [
			{ id: 'note-1', type: 'note', referenceSource: 'note' },
			{ id: 'kb-1', type: 'collection', referenceSource: 'knowledge' }
		];

		expect(isReferenceAttachmentSelected(files, { id: 'note-1', type: 'note' }, 'note')).toBe(true);
		expect(isReferenceAttachmentSelected(files, { id: 'note-1', type: 'note' }, 'knowledge')).toBe(
			false
		);
		expect(isReferenceAttachmentSelected(files, { id: 'note-2', type: 'note' }, 'note')).toBe(
			false
		);
	});

	test('all-selected state requires every visible item to be selected', () => {
		const files: ReferenceAttachment[] = [
			{ id: 'kb-1', type: 'collection', referenceSource: 'knowledge' },
			{ id: 'kb-2', type: 'collection', referenceSource: 'knowledge' }
		];

		expect(
			areReferenceAttachmentsFullySelected(
				files,
				[
					{ id: 'kb-1', type: 'collection' },
					{ id: 'kb-2', type: 'collection' }
				],
				'knowledge'
			)
		).toBe(true);

		expect(
			areReferenceAttachmentsFullySelected(
				files,
				[
					{ id: 'kb-1', type: 'collection' },
					{ id: 'kb-3', type: 'collection' }
				],
				'knowledge'
			)
		).toBe(false);
	});
});
