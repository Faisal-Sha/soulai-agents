CREATE OR REPLACE FUNCTION public.list_chat_threads(
    p_user_id uuid
)
RETURNS TABLE (
    thread_id text,
    preview text,
    message_count bigint,
    updated_at timestamptz
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN

    RETURN QUERY
    SELECT
        ch.thread_id,
        (
            SELECT c2.content
            FROM chat_history c2
            WHERE c2.thread_id = ch.thread_id
              AND c2.user_id = p_user_id
              AND c2.role = 'user'
            ORDER BY c2.created_at ASC
            LIMIT 1
        ) AS preview,
        COUNT(*)::bigint AS message_count,
        MAX(ch.created_at) AS updated_at
    FROM chat_history ch
    WHERE ch.user_id = p_user_id
    GROUP BY ch.thread_id
    ORDER BY MAX(ch.created_at) DESC;

END;
$$;

GRANT EXECUTE ON FUNCTION public.list_chat_threads(uuid)
TO anon, authenticated, service_role;
