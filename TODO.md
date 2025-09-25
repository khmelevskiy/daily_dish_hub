# Potential Enhancements (No Commitment)

- Add a page with receipts so that a cashier can quickly add items to the menu for reporting purposes and for generating simple charts (possibly another page in the admin panel).
- Add the ability to store several old menus and manage them (for example, make a previous menu active again, or set up menu configurations based on days of the week).
- Rebuild the public menu as a lightweight frontend package (for example, using Vite + Nunjucks for SSR) and bundle it the same way as the admin panel; this way we will have a single place for assets and reusable components. As part of the redesign, consider layering in a utility CSS framework (Tailwind, Bootstrap) to simplify responsive breakpoints while preserving the current look & feel.
- Add user management to the admin panel, with the ability to create new administrators, delete users, or update their passwords.
