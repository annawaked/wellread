import streamlit as st
from background.supabase_setup import supabase_setup, get_current_user_id
from account_components.goodreads_import import render_import_section

def account():
    supabase = supabase_setup()
    
    auth_response = supabase.auth.get_user()
    user = auth_response.user if auth_response else None

    if not user:
        render_auth_forms(supabase)
    else:
        user_id = user.id
        
        # res = supabase.table("profiles").select("*").eq("id", user_id).maybe_single().execute()
        # profile_data = res.data if res.data else {}
        # Fetch the profile
        res = supabase.table("profiles").select("*").eq("id", user_id).maybe_single().execute()

        # Check if res is None or if data is missing
        if res and hasattr(res, 'data') and res.data:
            profile_data = res.data
        else:
            # If no profile exists yet, give them empty defaults
            profile_data = {
                "handle": None,
                "bio": "",
                "reading_goal": 1
            }
        st.header(f"Profile: {profile_data.get('display_name', 'New Reader')}")
        
        with st.container(border=True):
            col1, col2 = st.columns(2)
            with col1:
                current_handle = profile_data.get('handle', "")
                is_locked = True if current_handle else False
                handle = st.text_input("Your @Handle", value=current_handle, disabled=is_locked)
                display_name = st.text_input("Display Name", value=profile_data.get('display_name', "New Reader"))
            with col2:
                goal = st.number_input("2026 Reading Goal", value=profile_data.get('reading_goal', 12), min_value=1)
                st.info(f"Target: {goal} books this year! 📚")            


            if st.button("Update Profile", use_container_width=True):
                # This updates YOUR table, linked by the Auth ID
                supabase.table("profiles").upsert({
                    "id": user_id,
                    "handle": handle,
                    "display_name": display_name,
                    "reading_goal": goal
                }).execute()
                st.success("Profile updated!")

            render_import_section()
            

        if st.button("Log Out", type="secondary"):
            supabase.auth.sign_out()
            
            st.cache_data.clear()
            
            st.session_state.clear()
            
            # 4. Force a full app reload
            st.rerun()
        
        render_password_change(supabase)


# Helper function for the Login/Signup UI
def render_auth_forms(supabase):
    st.header("Welcome to your Library")
    tab1, tab2 = st.tabs(["Login", "Create Account"])
    
    with tab1:
        with st.form("login"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Log In", use_container_width=True):
                try:
                    supabase.auth.sign_in_with_password({"email": email, "password": password})
                    st.rerun()
                except Exception as e:
                    st.error("Invalid email or password.")

    with tab2:
        with st.form("signup"):
            new_email = st.text_input("Email")
            new_pw = st.text_input("Password", type="password")
            if st.form_submit_button("Sign Up", use_container_width=True):
                try:
                    supabase.auth.sign_up({"email": new_email, "password": new_pw})
                    st.info("Success! Check your email for a confirmation link.")
                except Exception as e:
                    st.error(f"Error: {e}")

def render_password_change(supabase):
    st.divider()
    st.subheader("Account Security")
    
    with st.expander("🔐 Change Password"):
        st.write("Update your password below. You will remain logged in.")
        
        # Using a form helps prevent the app from refreshing until they hit 'Update'
        with st.form("password_reset_form", clear_on_submit=True):
            new_pw = st.text_input("New Password", type="password")
            confirm_pw = st.text_input("Confirm New Password", type="password")
            submit = st.form_submit_button("Update Password", use_container_width=True)
            
            if submit:
                if len(new_pw) < 6:
                    st.error("Password must be at least 6 characters.")
                elif new_pw != confirm_pw:
                    st.error("Passwords do not match.")
                else:
                    try:
                        # Supabase handles the current session automatically
                        supabase.auth.update_user({"password": new_pw})
                        st.success("Success! Your password has been updated.")
                        st.toast("Security updated.")
                    except Exception as e:
                        st.error(f"Error: {e}")
