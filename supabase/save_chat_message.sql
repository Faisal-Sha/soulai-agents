CREATE OR REPLACE FUNCTION public.save_chat_message(
    p_thread_id text,
    p_user_id uuid,
    p_role text,
    p_content text
)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN

    INSERT INTO chat_history(
        thread_id,
        user_id,
        role,
        content
    )
    VALUES(
        p_thread_id,
        p_user_id,
        p_role,
        p_content
    );

END;
$$;

GRANT EXECUTE ON FUNCTION public.save_chat_message(text, uuid, text, text)
TO anon, authenticated, service_role;
