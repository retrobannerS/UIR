======================== test session starts =========================
platform darwin -- Python 3.12.10, pytest-8.4.1, pluggy-1.6.0 
cachedir: .pytest_cache
rootdir: /Users/retrobanner/WorkBench/УИР/app
plugins: anyio-4.9.0, asyncio-1.0.0
asyncio: mode=Mode.STRICT, asyncio_default_fixture_loop_scope=None, 
         asyncio_default_test_loop_scope=function
collected 47 items                                                                                                                                           

test_preview_table_file PASSED                                  [  2%]
test_preview_with_custom_rows PASSED                            [  4%]
test_upload_table_for_user PASSED                               [  6%]
test_upload_table_with_custom_name PASSED                       [  8%]
test_upload_table_name_conflict PASSED                          [ 10%]
test_upload_invalid_extension PASSED                            [ 12%]
test_upload_excel_with_multiple_sheets PASSED                   [ 14%]
test_upload_empty_file PASSED                                   [ 17%]
test_read_own_tables PASSED                                     [ 19%]
test_rename_table PASSED                                        [ 21%]
test_delete_table PASSED                                        [ 23%]
test_unauthorized_user_cannot_access_tables PASSED              [ 25%]
test_create_user_success PASSED                                 [ 27%]
test_create_user_existing_username PASSED                       [ 29%]
test_create_user_invalid_input[1] PASSED                        [ 31%]
test_create_user_invalid_input[2] PASSED                        [ 34%]
test_create_user_invalid_input[3] PASSED                        [ 36%]
test_create_user_invalid_input[4] PASSED                        [ 38%]
test_create_user_invalid_input[5] PASSED                        [ 40%]
test_create_user_invalid_input[6] PASSED                        [ 42%]
test_login_access_token PASSED                                  [ 44%]
test_login_wrong_password PASSED                                [ 46%]
test_read_current_user PASSED                                   [ 48%]
test_check_username_exists PASSED                               [ 51%]
test_check_username_not_exists PASSED                           [ 53%]
test_update_username_success PASSED                             [ 55%]
test_update_username_regenerates_default_avatar PASSED          [ 57%]
test_update_username_preserves_custom_avatar PASSED             [ 59%]
test_update_username_to_taken_name PASSED                       [ 61%]
test_update_username_invalid_format PASSED                      [ 63%]
test_update_password_success PASSED                             [ 65%]
test_update_password_incorrect_old_password PASSED              [ 68%]
test_update_password_invalid_new[1] PASSED                      [ 70%]
test_update_password_invalid_new[2] PASSED                      [ 72%]
test_update_password_invalid_new[3] PASSED                      [ 74%]
test_update_password_invalid_new[4] PASSED                      [ 76%]
test_upload_avatar_success PASSED                               [ 78%]
test_upload_avatar_invalid_format PASSED                        [ 80%]
test_delete_avatar PASSED                                       [ 82%]
test_delete_default_avatar PASSED                               [ 85%]
test_register PASSED                                            [ 87%]
test_register_creates_default_avatar PASSED                     [ 89%]
test_get_existing_user PASSED                                   [ 91%]
test_convert_text_to_sql_users_query PASSED                     [ 93%]
test_convert_text_to_sql_products_count_query PASSED            [ 95%]
test_convert_text_to_sql_default_query PASSED                   [ 97%]
test_convert_text_to_sql_case_insensitivity PASSED              [100%]

======================== 47 passed in 18.53s =========================
