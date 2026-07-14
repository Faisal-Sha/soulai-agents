CREATE OR REPLACE FUNCTION public.search_memories(
    p_user_id uuid
)
RETURNS TABLE(
    category text,
    memory_key text,
    memory_value text,
    memory_text text,
    importance integer
)
LANGUAGE sql
SECURITY DEFINER
AS
$$

SELECT
    category,
    memory_key,
    memory_value,
    memory_text,
    importance

FROM memories

WHERE user_id = p_user_id

ORDER BY importance DESC,
         created_at DESC;

$$;