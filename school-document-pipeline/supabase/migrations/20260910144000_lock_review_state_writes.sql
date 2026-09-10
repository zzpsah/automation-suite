begin;

-- Review decisions must go through audited security-definer RPCs. Reviewers
-- should not be able to mutate protected workflow/publication columns directly.
drop policy if exists "reviewers update documents" on public.documents;
revoke update on public.documents from authenticated;

-- Keep reviewer read access and RPC-based writes. The backend worker/service
-- role is unaffected by this change and can continue ingestion/processing.

grant select on public.documents to authenticated;

grant execute on function public.save_document_review(uuid,jsonb) to authenticated;
grant execute on function public.accept_document_ai_suggestions(uuid) to authenticated;
grant execute on function public.reject_document_ai_suggestions(uuid) to authenticated;
grant execute on function public.approve_document_for_publication(uuid) to authenticated;
grant execute on function public.revoke_document_publication(uuid,text) to authenticated;
grant execute on function public.mark_document_reviewed(uuid) to authenticated;
grant execute on function public.reject_document_review(uuid,text) to authenticated;
grant execute on function public.request_document_ai_review(uuid) to authenticated;

commit;
