CREATE OR REPLACE FUNCTION public.get_user_context(
    p_user_id uuid,
    p_fields text[] DEFAULT NULL  -- TAYYAB: added this parameter
)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    result jsonb;
BEGIN

    SELECT jsonb_build_object(

        'profile',
        (
            SELECT jsonb_build_object(
                'id', p.id,
                'name', p.full_name,
                'email', p.email,
                'dob', p.dob
            )
            FROM public.profiles p
            WHERE p.id = p_user_id
        ),

        'subscription',
        (
            SELECT jsonb_build_object(
                'status', s.status,
                'plan_type', s.plan_type,
                'expires_at', s.expires_at,
                'is_premium',
                (
                    s.status IN ('active', 'trialing')
                )
            )
            FROM public.subscriptions s
            WHERE s.user_id = p_user_id
        ),

        'current_personal_matrix',
        (
            SELECT jsonb_build_object(
                'id', m.id,
                'title', m.title,
                'matrix_type', m.matrix_type,
                'birth_date', m.birth_date,
                'birth_date_partner', m.birth_date_partner,
                'matrix_data', m.matrix_data
            )
            FROM public.saved_matrices m
            WHERE m.user_id = p_user_id
              AND m.matrix_type = 'personal'
            ORDER BY m.created_at DESC
            LIMIT 1
        ),

        'metadata',
        jsonb_build_object(
            'user_exists',
            EXISTS (
                SELECT 1
                FROM public.profiles p
                WHERE p.id = p_user_id
            ),

            'has_subscription',
            EXISTS (
                SELECT 1
                FROM public.subscriptions s
                WHERE s.user_id = p_user_id
            ),

            'has_personal_matrix',
            EXISTS (
                SELECT 1
                FROM public.saved_matrices m
                WHERE m.user_id = p_user_id
                  AND m.matrix_type = 'personal'
            )
        )

    )
    INTO result;

    -- ===== TAYYAB: START — everything below this line is new =====
    -- No p_fields passed -> return everything, exactly like before.
    IF p_fields IS NULL THEN
        RETURN result;
    END IF;

    -- p_fields passed -> keep only those top-level keys (metadata always kept)
    RETURN (
        SELECT jsonb_object_agg(key, value)
        FROM jsonb_each(result)
        WHERE key = ANY(p_fields) OR key = 'metadata'
    );
    -- ===== TAYYAB: END =====

END;
$$;