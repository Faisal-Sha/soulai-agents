-- =============================================================================
-- SAVE DESTINY MATRIX (personal / this user only)
-- =============================================================================
-- Creates or updates the authenticated user's personal matrix in
-- public.saved_matrices.
--
-- IMPORTANT:
--   Use this ONLY for the authenticated user's own matrix
--   (matrix_type = 'personal').
--
-- Friend / relative matrices are NOT stored here.
-- They go to long-term memory instead (person_sarah_dob, person_sarah_matrix, ...).
-- =============================================================================

CREATE OR REPLACE FUNCTION public.save_matrix(
    p_user_id uuid,
    p_title text,
    p_matrix_type text,
    p_birth_date date,
    p_matrix_data jsonb,
    p_birth_date_partner date DEFAULT NULL
)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    saved_row public.saved_matrices%ROWTYPE;
    clean_type text;
BEGIN

    IF p_user_id IS NULL THEN
        RAISE EXCEPTION 'user_id is required';
    END IF;

    IF p_birth_date IS NULL THEN
        RAISE EXCEPTION 'birth_date is required';
    END IF;

    IF p_matrix_data IS NULL THEN
        RAISE EXCEPTION 'matrix_data is required';
    END IF;

    clean_type := COALESCE(NULLIF(trim(p_matrix_type), ''), 'personal');

    -- Guard: this RPC is for the user's own matrix only
    IF clean_type <> 'personal' THEN
        RAISE EXCEPTION
            'save_matrix only accepts matrix_type=personal (got %)',
            clean_type;
    END IF;

    -- Reuse the newest personal row when one already exists. The supplied
    -- saved_matrices schema has no unique (user_id, matrix_type) constraint,
    -- so a normal INSERT ... ON CONFLICT cannot be used here.
    SELECT *
    INTO saved_row
    FROM public.saved_matrices
    WHERE user_id = p_user_id
      AND matrix_type = 'personal'
    ORDER BY created_at DESC
    LIMIT 1
    FOR UPDATE;

    IF FOUND THEN
        UPDATE public.saved_matrices
        SET
            title = COALESCE(NULLIF(trim(p_title), ''), 'My Destiny Matrix'),
            birth_date = p_birth_date,
            birth_date_partner = p_birth_date_partner,
            matrix_data = p_matrix_data,
            updated_at = now()
        WHERE id = saved_row.id
        RETURNING * INTO saved_row;
    ELSE
        INSERT INTO public.saved_matrices (
            user_id,
            title,
            matrix_type,
            birth_date,
            birth_date_partner,
            matrix_data
        )
        VALUES (
            p_user_id,
            COALESCE(NULLIF(trim(p_title), ''), 'My Destiny Matrix'),
            'personal',
            p_birth_date,
            p_birth_date_partner,
            p_matrix_data
        )
        RETURNING * INTO saved_row;
    END IF;

    RETURN jsonb_build_object(
        'id', saved_row.id,
        'user_id', saved_row.user_id,
        'title', saved_row.title,
        'matrix_type', saved_row.matrix_type,
        'birth_date', saved_row.birth_date,
        'birth_date_partner', saved_row.birth_date_partner,
        'matrix_data', saved_row.matrix_data,
        'created_at', saved_row.created_at,
        'updated_at', saved_row.updated_at
    );

END;
$$;

GRANT EXECUTE ON FUNCTION public.save_matrix(uuid, text, text, date, jsonb, date)
TO anon, authenticated, service_role;
