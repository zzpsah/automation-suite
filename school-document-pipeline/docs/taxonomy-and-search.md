# Durable Taxonomy and Search

## Stable records

Every document stores an immutable-style `category_key`, such as `district_office` or `payment_fee`. Website labels are not used as database identities, so a page rename, navigation change, or translated label does not rewrite or lose document records.

## Versioned category definitions

`document_category_definitions` stores display names, aliases, office terms, content terms, and ordering as versions. Existing versions cannot be rewritten. To change a category:

1. set `valid_to` on the current version;
2. insert the next version with the same `category_key` and a higher version number;
3. keep the old row for audit and rollback.

Do not delete old definitions. A completely new category first receives a stable key in `document_categories`, followed by its version-1 definition.

## Classification

The Apps Script worker loads the current definitions at processing time. Issuing-office matches receive the highest weight, then content terms and aliases. The result records the key, visible label, source (`rule`, `manual`, `import`, or `legacy`), and confidence.

Rule suggestions never publish a document. Human review remains required.

## Search

The database maintains a GIN-indexed `search_vector` over document fields. The public view also returns `search_text`, which combines subject, description, issuing authority, reference number, required action, category label, aliases, office terms, and content terms.

The website searches `search_text` and filters by `category_key`. A category label or alias can therefore change without editing historical documents or rebuilding page HTML.

## Page independence

The public page is a replaceable shell. Its CSS, runtime, and public connection configuration are separate assets. The source of truth remains Supabase and Drive, so pages can move, be redesigned, or be split into new navigation sections without moving document records.
