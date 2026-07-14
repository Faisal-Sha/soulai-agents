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
AS $$
BEGIN

    INSERT INTO memories(
        user_id,
        category,
        memory_key,
        memory_value,
        memory_text,
        importance
    )
    VALUES(
        p_user_id,
        p_category,
        p_memory_key,
        p_memory_value,
        p_memory_text,
        p_importance
    );

END;
$$;