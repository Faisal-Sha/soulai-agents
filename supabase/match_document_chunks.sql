-- Run this entire script in Supabase: SQL Editor -> New query -> Run
-- Table: document_chunks
-- Embedding model: text-embedding-3-small (1536 dimensions)

create extension if not exists vector;

-- Optional: confirm embedding column type (should be "vector", not "text")
-- select column_name, data_type, udt_name
-- from information_schema.columns
-- where table_schema = 'public' and table_name = 'document_chunks';

create or replace function public.match_document_chunks(
  query_embedding vector(1536),
  match_threshold float default 0.3,
  match_count int default 5
)
returns table (
  id uuid,
  document_id uuid,
  chunk_index int,
  content text,
  summary text,
  metadata jsonb,
  token_count int,
  similarity float
)
language sql
stable
as $$
  select
    dc.id,
    dc.document_id,
    dc.chunk_index,
    dc.content,
    dc.summary,
    dc.metadata,
    dc.token_count,
    1 - (dc.embedding <=> query_embedding) as similarity
  from public.document_chunks dc
  where dc.embedding is not null
    and 1 - (dc.embedding <=> query_embedding) > match_threshold
  order by dc.embedding <=> query_embedding
  limit match_count;
$$;

-- If embedding is stored as TEXT instead of vector, use this version instead:
-- replace `dc.embedding` with `dc.embedding::vector` in the function above.

grant usage on schema public to anon, authenticated;
grant select on table public.document_chunks to anon, authenticated;
grant execute on function public.match_document_chunks(vector, float, int) to anon, authenticated;

alter table public.document_chunks enable row level security;

drop policy if exists "Allow read document_chunks" on public.document_chunks;
create policy "Allow read document_chunks"
on public.document_chunks
for select
to anon, authenticated
using (true);

-- Optional performance index (run after you have enough rows)
-- create index if not exists document_chunks_embedding_idx
-- on public.document_chunks
-- using ivfflat (embedding vector_cosine_ops)
-- with (lists = 100);
