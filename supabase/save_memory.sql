-- =============================================================================
-- UPSERT memory by (user_id, memory_key)
-- =============================================================================
-- Why upsert?
-- If we first saved a bad vague note for key "person_ali_relation",
-- and later the user clearly says "Ali is my uncle", we UPDATE the same key
-- instead of stacking duplicate junk rows.
--
-- If CREATE UNIQUE INDEX fails because duplicates already exist, run once:
--
--   DELETE FROM memories a
--   USING memories b
--   WHERE a.user_id = b.user_id
--     AND a.memory_key = b.memory_key
--     AND a.created_at < b.created_at;
--
-- Optional: remove vague junk rows:
--
--   DELETE FROM memories
--   WHERE memory_text ILIKE '%person in conversation%'
--      OR memory_text ILIKE '%mentioned that the name%';
-- =============================================================================

-- One fact key per user (e.g. person_ali_relation)
CREATE UNIQUE INDEX IF NOT EXISTS memories_user_id_memory_key_uidx
ON public.memories (user_id, memory_key);


CREATE OR REPLACE FUNCTION public.save_memory(
    p_user_id uuid,
    p_category text,
    p_memory_key text,
    p_memory_value text,
    p_memory_text text,
    p_importance integer DEFAULT 3
)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN

    INSERT INTO memories(
        user_id,
        category,
        memory_key,
        memory_value,
        memory_text,
        importance,
        updated_at
    )
    VALUES(
        p_user_id,
        p_category,
        p_memory_key,
        p_memory_value,
        p_memory_text,
        p_importance,
        now()
    )
    ON CONFLICT (user_id, memory_key)
    DO UPDATE SET
        category = EXCLUDED.category,
        memory_value = EXCLUDED.memory_value,
        memory_text = EXCLUDED.memory_text,
        importance = EXCLUDED.importance,
        updated_at = now();

END;
$$;

GRANT EXECUTE ON FUNCTION public.save_memory(uuid, text, text, text, text, integer)
TO anon, authenticated, service_role;
