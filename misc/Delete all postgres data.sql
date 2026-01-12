DO $$ 
DECLARE 
    table_name TEXT; 
BEGIN 
    FOR table_name IN 
        (SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname = 'public') 
    LOOP 
        EXECUTE 'TRUNCATE TABLE ' || quote_ident(table_name) || ' CASCADE'; 
    END LOOP; 
END $$;

