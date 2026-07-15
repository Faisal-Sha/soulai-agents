CREATE OR REPLACE FUNCTION public.get_chat_history(
    p_thread_id text,
    p_user_id uuid
)
RETURNS TABLE (
    id uuid,
    thread_id text,
    user_id uuid,
    role text,
    content text,
    created_at timestamptz
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN

    RETURN QUERY
    SELECT
        ch.id,
        ch.thread_id,
        ch.user_id,
        ch.role,
        ch.content,
        ch.created_at
    FROM chat_history ch
    WHERE ch.thread_id = p_thread_id
      AND ch.user_id = p_user_id
    ORDER BY ch.created_at ASC;

END;
$$;

GRANT EXECUTE ON FUNCTION public.get_chat_history(text, uuid)
TO anon, authenticated, service_role;
