create table if not exists public.chat_history (

    id uuid primary key default gen_random_uuid(),

    thread_id text not null,

    user_id uuid not null references auth.users(id) on delete cascade,

    role text not null,

    content text not null,

    created_at timestamptz default now()

);

-- RLS may already be enabled in the dashboard.
-- Direct table inserts from the API (anon key, no user JWT) fail with 42501.
-- Use save_chat_message / get_chat_history (SECURITY DEFINER) instead.

alter table public.chat_history enable row level security;
