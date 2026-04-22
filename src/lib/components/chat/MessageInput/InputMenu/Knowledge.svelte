<script lang="ts">
	import { onMount, tick, getContext } from 'svelte';
	import type { Readable } from 'svelte/store';

	import { decodeString } from '$lib/utils';
	import {
		areReferenceAttachmentsFullySelected,
		isReferenceAttachmentSelected,
		type ReferenceAttachment
	} from '$lib/utils/referenceAttachments';

	import { getKnowledgeBases, searchKnowledgeFilesById } from '$lib/apis/knowledge';

	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import Database from '$lib/components/icons/Database.svelte';
	import DocumentPage from '$lib/components/icons/DocumentPage.svelte';
	import Check from '$lib/components/icons/Check.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import Loader from '$lib/components/common/Loader.svelte';
	import ChevronDown from '$lib/components/icons/ChevronDown.svelte';
	import ChevronRight from '$lib/components/icons/ChevronRight.svelte';

	const i18n = getContext<Readable<{ t: (key: string) => string }>>('i18n');

	export let onSelect: (e: ReferenceAttachment) => void = () => {};
	export let onSelectAll: (_context?: {
		items: ReferenceAttachment[];
		total: number | null;
	}) => Promise<void> = async () => {};
	export let selectedReferences: ReferenceAttachment[] = [];

	let loaded = false;
	let selectedIdx = 0;

	let selectedItem: ReferenceAttachment | null = null;

	let selectedFileItemsPage = 1;

	let selectedFileItems: ReferenceAttachment[] | null = null;
	let selectedFileItemsTotal: number | null = null;

	let selectedFileItemsLoading = false;
	let selectedFileAllItemsLoaded = false;

	$: if (selectedItem) {
		initSelectedFileItems();
	}

	const initSelectedFileItems = async () => {
		selectedFileItemsPage = 1;
		selectedFileItems = null;
		selectedFileItemsTotal = null;
		selectedFileAllItemsLoaded = false;
		selectedFileItemsLoading = false;
		await tick();
		await getSelectedFileItemsPage();
	};

	const loadMoreSelectedFileItems = async () => {
		if (selectedFileAllItemsLoaded) return;
		selectedFileItemsPage += 1;
		await getSelectedFileItemsPage();
	};

	const getSelectedFileItemsPage = async () => {
		if (!selectedItem) return;
		selectedFileItemsLoading = true;

		const res = await searchKnowledgeFilesById(
			localStorage.token,
			String(selectedItem.id ?? ''),
			null,
			null,
			null,
			null,
			selectedFileItemsPage
		).catch(() => {
			return null;
		});

		if (res) {
			selectedFileItemsTotal = res.total;
			const pageItems: ReferenceAttachment[] = res.items ?? [];

			if ((pageItems ?? []).length === 0) {
				selectedFileAllItemsLoaded = true;
			} else {
				selectedFileAllItemsLoaded = false;
			}

			if (selectedFileItems) {
				selectedFileItems = [...selectedFileItems, ...pageItems];
			} else {
				selectedFileItems = pageItems;
			}
		}

		selectedFileItemsLoading = false;
		return res;
	};

	let page = 1;
	let items: ReferenceAttachment[] | null = null;
	let total: number | null = null;

	let itemsLoading = false;
	let allItemsLoaded = false;
	let allCollectionsSelected = false;
	let selectedCollectionCount = 0;

	const getItemName = (item: ReferenceAttachment) => decodeString(String(item?.name ?? ''));

	const getItemDescription = (item: ReferenceAttachment) =>
		typeof item?.description === 'string' ? item.description : getItemName(item);

	const getFileMetaName = (file: ReferenceAttachment) =>
		decodeString(String((file?.meta as { name?: string } | undefined)?.name ?? ''));

	$: selectedCollectionCount = selectedReferences.filter(
		(item) => item?.type === 'collection'
	).length;
	$: allCollectionsSelected =
		total !== null
			? selectedCollectionCount >= total && total > 0
			: areReferenceAttachmentsFullySelected(
					selectedReferences,
					(items ?? []).map((item) => ({
						type: 'collection',
						...item
					})),
					'knowledge'
				);

	$: if (loaded) {
		init();
	}

	const init = async () => {
		reset();
		await tick();
		await getItemsPage();
	};

	const reset = () => {
		page = 1;
		items = null;
		total = null;
		allItemsLoaded = false;
		itemsLoading = false;
	};

	const loadMoreItems = async () => {
		if (allItemsLoaded) return;
		page += 1;
		await getItemsPage();
	};

	const getItemsPage = async () => {
		itemsLoading = true;
		const res = await getKnowledgeBases(localStorage.token, page).catch(() => {
			return null;
		});

		if (res) {
			total = res.total;
			const pageItems: ReferenceAttachment[] = res.items ?? [];

			if ((pageItems ?? []).length === 0) {
				allItemsLoaded = true;
			} else {
				allItemsLoaded = false;
			}

			if (items) {
				items = [...items, ...pageItems];
			} else {
				items = pageItems;
			}
		}

		itemsLoading = false;
		return res;
	};

	onMount(async () => {
		await tick();
		loaded = true;
	});
</script>

{#if loaded && items !== null}
	<div class="flex flex-col gap-0.5">
		{#if items.length === 0}
			<div class="py-4 text-center text-sm text-gray-500 dark:text-gray-400">
				{$i18n.t('No knowledge bases found.')}
			</div>
		{:else}
			<button
				class="px-2.5 py-1 rounded-xl w-full text-left flex justify-between items-center text-sm text-sky-600 dark:text-sky-300 border {allCollectionsSelected
					? 'bg-sky-50 dark:bg-sky-900/30 border-sky-200/60 dark:border-sky-500/30'
					: 'border-transparent hover:bg-sky-50 hover:dark:bg-sky-900/30'}"
				type="button"
				aria-pressed={allCollectionsSelected}
				on:click={async () => {
					await onSelectAll({
						items: (items ?? []).map((item) => ({
							type: 'collection',
							...item
						})),
						total
					});
				}}
			>
				<div class="flex items-center gap-1.5">
					<Database className="size-4" />
					<div>{$i18n.t('All')}</div>
				</div>
				<div class="flex items-center gap-2">
					{#if total !== null}
						<div class="text-xs text-gray-500 dark:text-gray-400">{total}</div>
					{/if}
					{#if allCollectionsSelected}
						<div
							class="size-5 rounded-full bg-sky-500/10 text-sky-600 dark:text-sky-300 flex items-center justify-center"
						>
							<Check className="size-3" strokeWidth="2" />
						</div>
					{/if}
				</div>
			</button>

			{#each items as item, idx (item.id)}
				{@const itemSelected = isReferenceAttachmentSelected(
					selectedReferences,
					{
						type: 'collection',
						...item
					},
					'knowledge'
				)}
				<div
					class="px-2.5 py-1 rounded-xl w-full text-left flex justify-between items-center text-sm border {itemSelected
						? 'bg-sky-50 dark:bg-sky-900/30 border-sky-200/60 dark:border-sky-500/30 text-sky-700 dark:text-sky-200'
						: idx === selectedIdx
							? 'bg-gray-50 dark:bg-gray-800 dark:text-gray-100 selected-command-option-button border-transparent'
							: 'border-transparent'}"
				>
					<button
						class="w-full flex-1"
						type="button"
						on:click={() => {
							onSelect({
								type: 'collection',
								...item
							});
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
							class="w-full text-left flex items-center gap-1 {itemSelected
								? 'text-sky-700 dark:text-sky-200'
								: 'text-black dark:text-gray-100'}"
						>
							<Tooltip content={$i18n.t('Collection')} placement="top">
								<Database className="size-4" />
							</Tooltip>

							<Tooltip
								content={getItemDescription(item)}
								placement="top-start"
								className="flex flex-1 min-w-0"
							>
								<div class="line-clamp-1 flex-1 text-sm">
									{getItemName(item)}
								</div>
							</Tooltip>
						</div>
					</button>

					<div class="ml-2 flex items-center gap-1.5">
						{#if itemSelected}
							<div
								class="size-5 rounded-full bg-sky-500/10 text-sky-600 dark:text-sky-300 flex items-center justify-center"
							>
								<Check className="size-3" strokeWidth="2" />
							</div>
						{/if}
						<Tooltip content={$i18n.t('Show Files')} placement="top">
							<button
								type="button"
								class="opacity-50 hover:opacity-100 transition"
								on:click={() => {
									if (selectedItem && selectedItem.id === item.id) {
										selectedItem = null;
									} else {
										selectedItem = item;
									}
								}}
							>
								{#if selectedItem && selectedItem.id === item.id}
									<ChevronDown className="size-3" />
								{:else}
									<ChevronRight className="size-3" />
								{/if}
							</button>
						</Tooltip>
					</div>
				</div>

				{#if selectedItem && selectedItem.id === item.id}
					<div class="pl-3 mb-1 flex flex-col gap-0.5">
						{#if selectedFileItems === null && selectedFileItemsTotal === null}
							<div class=" py-1 flex justify-center">
								<Spinner className="size-3" />
							</div>
						{:else if selectedFileItemsTotal === 0}
							<div class=" text-xs text-gray-500 dark:text-gray-400 italic py-0.5 px-2">
								{$i18n.t('No files in this knowledge base.')}
							</div>
						{:else}
							{#each selectedFileItems as file, fileIdx (file.id)}
								{@const fileSelected = isReferenceAttachmentSelected(
									selectedReferences,
									{
										type: 'file',
										name: getFileMetaName(file),
										...file
									},
									'knowledge'
								)}
								<button
									class="px-2.5 py-1 rounded-xl w-full text-left flex justify-between items-center text-sm border {fileSelected
										? 'bg-sky-50 dark:bg-sky-900/30 border-sky-200/60 dark:border-sky-500/30 text-sky-700 dark:text-sky-200'
										: 'border-transparent hover:bg-gray-50 hover:dark:bg-gray-800 hover:dark:text-gray-100'}"
									type="button"
									aria-pressed={fileSelected}
									on:click={() => {
										onSelect({
											type: 'file',
											name: getFileMetaName(file),
											...file
										});
									}}
								>
									<div
										class="flex items-center gap-1.5 {fileSelected
											? 'text-sky-700 dark:text-sky-200'
											: 'text-black dark:text-gray-100'}"
									>
										<Tooltip content={$i18n.t('Collection')} placement="top">
											<DocumentPage className="size-4" />
										</Tooltip>

										<Tooltip content={getFileMetaName(file)} placement="top-start">
											<div class="line-clamp-1 flex-1 text-sm">
												{getFileMetaName(file)}
											</div>
										</Tooltip>
									</div>
									{#if fileSelected}
										<div
											class="size-5 rounded-full bg-sky-500/10 text-sky-600 dark:text-sky-300 flex items-center justify-center"
										>
											<Check className="size-3" strokeWidth="2" />
										</div>
									{/if}
								</button>
							{/each}

							{#if !selectedFileAllItemsLoaded && !selectedFileItemsLoading}
								<Loader
									on:visible={async (e) => {
										if (!selectedFileItemsLoading) {
											await loadMoreSelectedFileItems();
										}
									}}
								>
									<div
										class="w-full flex justify-center py-4 text-xs animate-pulse items-center gap-2"
									>
										<Spinner className=" size-3" />
										<div class=" ">{$i18n.t('Loading...')}</div>
									</div>
								</Loader>
							{/if}
						{/if}
					</div>
				{/if}
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
		{/if}
	</div>
{:else}
	<div class="py-4.5">
		<Spinner />
	</div>
{/if}
