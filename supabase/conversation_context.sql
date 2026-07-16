-- =============================================================================
-- CONVERSATION CONTEXT
-- =============================================================================
-- Stores TEMPORARY multi-turn work for one chat thread.
--
-- Example: User asks "Read Asim's matrix" but we still need Asim's date of birth.
-- We save that "waiting" state here so it survives browser close / server restart.
--
-- This is NOT long-term memory (friends, goals, etc.).
-- This is NOT chat history (full messages).
-- This is only: "what are we waiting for right now?"
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.conversation_context (

    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Which chat thread this pending work belongs to
    thread_id text NOT NULL,

    -- Which user owns this thread
    user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- waiting  = we asked the user something and are waiting for their reply
    -- ready    = all slots filled; ready to resume the original task
    -- cleared  = cancelled / finished (row may still exist until deleted)
    status text NOT NULL DEFAULT 'waiting'
        CHECK (status IN ('waiting', 'ready', 'cleared')),

    -- What the user originally wanted, e.g. "friend_matrix"
    intent text NOT NULL,

    -- JSON object of known + missing fields, e.g.
    -- { "friend_name": "Asim", "friend_dob": null }
    slots jsonb NOT NULL DEFAULT '{}'::jsonb,

    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),

    -- One active context per thread (simplest rule for beginners)
    UNIQUE (thread_id)
);

ALTER TABLE public.conversation_context ENABLE ROW LEVEL SECURITY;


-- -----------------------------------------------------------------------------
-- GET: load the current pending context for a thread
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.get_conversation_context(
    p_thread_id text,
    p_user_id uuid
)
RETURNS TABLE (
    id uuid,
    thread_id text,
    user_id uuid,
    status text,
    intent text,
    slots jsonb,
    created_at timestamptz,
    updated_at timestamptz
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    RETURN QUERY
    SELECT
        cc.id,
        cc.thread_id,
        cc.user_id,
        cc.status,
        cc.intent,
        cc.slots,
        cc.created_at,
        cc.updated_at
    FROM conversation_context cc
    WHERE cc.thread_id = p_thread_id
      AND cc.user_id = p_user_id
      AND cc.status IN ('waiting', 'ready')
    LIMIT 1;
END;
$$;

GRANT EXECUTE ON FUNCTION public.get_conversation_context(text, uuid)
TO anon, authenticated, service_role;


-- -----------------------------------------------------------------------------
-- UPSERT: create or update pending context for a thread
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.upsert_conversation_context(
    p_thread_id text,
    p_user_id uuid,
    p_status text,
    p_intent text,
    p_slots jsonb
)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    INSERT INTO conversation_context (
        thread_id,
        user_id,
        status,
        intent,
        slots,
        updated_at
    )
    VALUES (
        p_thread_id,
        p_user_id,
        p_status,
        p_intent,
        COALESCE(p_slots, '{}'::jsonb),
        now()
    )
    ON CONFLICT (thread_id)
    DO UPDATE SET
        user_id = EXCLUDED.user_id,
        status = EXCLUDED.status,
        intent = EXCLUDED.intent,
        slots = EXCLUDED.slots,
        updated_at = now();
END;
$$;

GRANT EXECUTE ON FUNCTION public.upsert_conversation_context(text, uuid, text, text, jsonb)
TO anon, authenticated, service_role;


-- -----------------------------------------------------------------------------
-- CLEAR: remove pending context when the task is done or abandoned
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.clear_conversation_context(
    p_thread_id text,
    p_user_id uuid
)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    DELETE FROM conversation_context
    WHERE thread_id = p_thread_id
      AND user_id = p_user_id;
END;
$$;

GRANT EXECUTE ON FUNCTION public.clear_conversation_context(text, uuid)
TO anon, authenticated, service_role;
