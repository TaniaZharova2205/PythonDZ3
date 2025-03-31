import streamlit as st
import frontend_utils as fu

if "session" not in st.session_state:
    st.session_state.session = fu.get_requests_session()
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

API_URL = st.secrets["API_URL"] if "API_URL" in st.secrets else "http://urlshort_backend:8000"

st.title("Сервис сокращения ссылок")

menu = st.sidebar.radio("Навигация", ["Вход/Регистрация", "Мои ссылки", "Создать ссылку", "Аналитика", "Удалить аккаунт", "Выход"])

if menu == "Вход/Регистрация":
    st.header("Вход/Регистрация")
    choice = st.radio("Выберите действие", ["Вход", "Регистрация"])
    username = st.text_input("Имя пользователя")
    password = st.text_input("Пароль", type="password")
    if choice == "Регистрация":
        email = st.text_input("Email (опционально)")
        if st.button("Зарегистрироваться"):
            result = fu.register(API_URL, username, password, email)
            if result.get("detail"):
                st.error(result["detail"])
            else:
                st.success("Регистрация успешна! Теперь выполните вход.")
    else:
        if st.button("Войти"):
            result = fu.login(API_URL, username, password, st.session_state.session)
            if result.get("detail") and result["detail"] != "Успешный вход":
                st.error(result["detail"])
            else:
                st.session_state.logged_in = True
                st.success("Вход выполнен успешно!")

elif menu == "Мои ссылки":
    if not st.session_state.logged_in:
        st.warning("Войдите в систему, чтобы увидеть ваши ссылки")
    else:
        st.header("Ваши ссылки")
        links_container = st.empty()
        links = fu.get_links(API_URL, st.session_state.session)
        if links:
            import pandas as pd
            df = pd.DataFrame(links)
            internal_api_url = st.secrets["API_URL"] if "API_URL" in st.secrets else "http://localhost:8000"
            public_api_url = internal_api_url.replace("http://api:8000", "http://localhost:8000")
            df["Short URL"] = public_api_url + "/" + df["short_code"].astype(str)
            links_container.table(df)
            st.write("Нажмите кнопку «Удалить» для удаления соответствующей ссылки:")
            for link in links:
                cols = st.columns([3, 5, 2])
                with cols[0]:
                    st.write(f"**Short Code:** {link['short_code']}")
                with cols[1]:
                    st.write(f"**Original URL:** {link['original_url']}")
                with cols[2]:
                    if st.button("Удалить", key=f"del_{link['id']}"):
                        result = fu.delete_link(API_URL, link["short_code"], st.session_state.session)
                        if result.get("detail"):
                            st.error(result["detail"])
                        else:
                            st.success(f"Ссылка {link['short_code']} удалена")
                            # Обновляем таблицу, получая заново список ссылок:
                            updated_links = fu.get_links(API_URL, st.session_state.session)
                            if updated_links:
                                df_updated = pd.DataFrame(updated_links)
                                df_updated["Short URL"] = public_api_url + "/" + df_updated["short_code"].astype(str)
                                links_container.table(df_updated)
                            else:
                                links_container.info("У вас пока нет сокращенных ссылок.")
        else:
            st.info("У вас пока нет сокращенных ссылок.")

elif menu == "Создать ссылку":
    if not st.session_state.logged_in:
        st.warning("Войдите в систему, чтобы создавать ссылки")
    else:
        st.header("Создание новой ссылки")
        original_url = st.text_input("Оригинальный URL")
        custom_alias = st.text_input("Кастомный alias (необязательно)")
        expires_in_days = st.number_input("Срок жизни ссылки (в днях, 0 - бессрочно)", min_value=0, value=0)
        if st.button("Создать"):
            payload = {
                "original_url": original_url,
                "custom_alias": custom_alias if custom_alias != "" else None,
                "expires_in_days": expires_in_days if expires_in_days > 0 else None,
            }
            result = fu.create_link(API_URL, payload, st.session_state.session)
            if result.get("detail"):
                st.error(result["detail"])
            else:
                st.success(f"Ссылка создана: {result['short_code']}")

elif menu == "Аналитика":
    if not st.session_state.logged_in:
        st.warning("Войдите, чтобы просмотреть аналитику")
    else:
        st.header("Аналитика по ссылкам")
        links = fu.get_links(API_URL, st.session_state.session)
        if links:
            import pandas as pd
            df = pd.DataFrame(links)
            if "short_code" in df.columns and "access_count" in df.columns:
                df = df.rename(columns={"short_code": "Ссылка", "access_count": "Количество переходов"})
                st.bar_chart(df.set_index("Ссылка")["Количество переходов"])
            else:
                st.info("Нет данных для аналитики (нет столбцов short_code или access_count).")
        else:
            st.info("Нет данных для отображения аналитики.")

elif menu == "Удалить аккаунт":
    if not st.session_state.logged_in:
        st.warning("Войдите в систему, чтобы удалить аккаунт")
    else:
        st.header("Удаление аккаунта")
        st.warning("Внимание: эта операция безвозвратно удалит ваш профиль и все связанные ссылки.")
        if st.button("Удалить аккаунт"):
            resp = fu.delete_user(API_URL, st.session_state.session)
            if resp.get("message") == "Пользователь удалён":
                st.success("Аккаунт удалён. Пожалуйста, перезайдите.")
                st.session_state.logged_in = False
            else:
                st.error(resp.get("detail") or "Неизвестная ошибка при удалении аккаунта")

elif menu == "Выход":
    if st.button("Выйти"):
        fu.logout(API_URL, st.session_state.session)
        st.session_state.logged_in = False
        st.success("Вы вышли из системы")