<script lang="ts">
	import dayjs from 'dayjs';
	import { onMount, tick, getContext } from 'svelte';
	import type { Readable } from 'svelte/store';

	import { decodeString } from '$lib/utils';
	import { getNoteList } from '$lib/apis/notes';
	import {
		areReferenceAttachmentsFullySelected,
		isReferenceAttachmentSelected,
		type ReferenceAttachment
	} from '$lib/utils/referenceAttachments';

	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import PageEdit from '$lib/components/icons/PageEdit.svelte';
	import Check from '$lib/components/icons/Check.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import Loader from '$lib/components/common/Loader.svelte';

	const i18n = getContext<Readable<{ t: (key: string) => string }>>('i18n');

	export let onSelect: (e: ReferenceAttachment) => void = () => {};
	export let onSelectAll: (_context?: {
		items: ReferenceAttachment[];
	}) => Promise<void> = async () => {};
	export let selectedReferences: ReferenceAttachment[] = [];

	let loaded = false;

	let items: ReferenceAttachment[] = [];
	let selectedIdx = 0;

	let page = 1;
	let itemsLoading = false;
	let allItemsLoaded = false;
	let allVisibleNotesSelected = false;

	const getItemName = (item: ReferenceAttachment) => decodeString(String(item?.name ?? ''));

	const getItemDescription = (item: ReferenceAttachment) =>
		typeof item?.description === 'string' ? item.description : getItemName(item);

	$: allVisibleNotesSelected = areReferenceAttachmentsFullySelected(
		selectedReferences,
		items,
		'note'
	);

	const loadMoreItems = async () => {
		if (allItemsLoaded) return;
		page += 1;
		await getItemsPage();
	};

	const getItemsPage = async () => {
		itemsLoading = true;
		const res: any[] = await getNoteList(localStorage.token, page).catch(() => {
			return [];
		});

		if ((res ?? []).length === 0) {
			allItemsLoaded = true;
		} else {
			allItemsLoaded = false;
		}

		items = [
			...items,
			...res.map((note: any) => {
				return {
					...note,
					type: 'note',
					name: note.title,
					description: dayjs(note.updated_at / 1000000).fromNow()
				};
			})
		];

		itemsLoading = false;

		return res;
	};

	onMount(async () => {
		await getItemsPage();
		await tick();

		loaded = true;
	});
</script>

{#if loaded}
	{#if items.length === 0}
		<div class="text-center text-xs text-gray-500 py-3">{$i18n.t('No notes found')}</div>
	{:else}
		<div class="flex flex-col gap-0.5">
			<button
				class="px-2.5 py-1 rounded-xl w-full text-left flex justify-between items-center text-sm text-sky-600 dark:text-sky-300 border {allVisibleNotesSelected
					? 'bg-sky-50 dark:bg-sky-900/30 border-sky-200/60 dark:border-sky-500/30'
					: 'border-transparent hover:bg-sky-50 hover:dark:bg-sky-900/30'}"
				type="button"
				aria-pressed={allVisibleNotesSelected}
				on:click={async () => {
					await onSelectAll({
						items
					});
				}}
			>
				<div class="flex items-center gap-1.5">
					<PageEdit className="size-4" />
					<div>{$i18n.t('All')}</div>
				</div>
				{#if allVisibleNotesSelected}
					<div
						class="size-5 rounded-full bg-sky-500/10 text-sky-600 dark:text-sky-300 flex items-center justify-center"
					>
						<Check className="size-3" strokeWidth="2" />
					</div>
				{/if}
			</button>

			{#each items as item, idx}
				{@const itemSelected = isReferenceAttachmentSelected(selectedReferences, item, 'note')}
				<button
					class="px-2.5 py-1 rounded-xl w-full text-left flex justify-between items-center text-sm border {itemSelected
						? 'bg-sky-50 dark:bg-sky-900/30 border-sky-200/60 dark:border-sky-500/30 text-sky-700 dark:text-sky-200'
						: idx === selectedIdx
							? 'bg-gray-50 dark:bg-gray-800 dark:text-gray-100 selected-command-option-button border-transparent'
							: 'border-transparent'}"
					type="button"
					on:click={() => {
						onSelect(item);
					}}
					on:mousemove={() => {
						selectedIdx = idx;
					}}
					on:mouseleave={() => {
						if (idx === 0) {
							selectedIdx = -1;
						}
					}}
					aria-pressed={itemSelected}
					data-selected={idx === selectedIdx}
				>
					<div
						class="flex items-center gap-1.5 {itemSelected
							? 'text-sky-700 dark:text-sky-200'
							: 'text-black dark:text-gray-100'}"
					>
						<Tooltip content={$i18n.t('Note')} placement="top">
							<PageEdit className="size-4" />
						</Tooltip>

						<Tooltip content={getItemDescription(item)} placement="top-start">
							<div class="line-clamp-1 flex-1">
								{getItemName(item)}
							</div>
						</Tooltip>
					</div>
					{#if itemSelected}
						<div
							class="size-5 rounded-full bg-sky-500/10 text-sky-600 dark:text-sky-300 flex items-center justify-center"
						>
							<Check className="size-3" strokeWidth="2" />
						</div>
					{/if}
				</button>
			{/each}

			{#if !allItemsLoaded}
				<Loader
					on:visible={(e) => {
						if (!itemsLoading) {
							loadMoreItems();
						}
					}}
				>
					<div class="w-full flex justify-center py-4 text-xs animate-pulse items-center gap-2">
						<Spinner className=" size-4" />
						<div class=" ">{$i18n.t('Loading...')}</div>
					</div>
				</Loader>
			{/if}
		</div>
	{/if}
{:else}
	<div class="py-4.5">
		<Spinner />
	</div>
{/if}
