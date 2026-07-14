create table public.memories (
    id uuid primary key default gen_random_uuid(),

    user_id uuid not null references auth.users(id) on delete cascade,

    category text not null,

    memory_key text not null,

    memory_value text not null,

    memory_text text not null,

    importance integer not null default 3,

    created_at timestamptz not null default now(),

    updated_at timestamptz not null default now()
);

create trigger set_updated_at_memories
before update on memories
for each row
execute function handle_updated_at();