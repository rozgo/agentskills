# Leptos Router Reference

## Table of Contents
- [Setup](#setup)
- [Route Definition](#route-definition)
- [Nested Routes](#nested-routes)
- [Route Parameters](#route-parameters)
- [Query Parameters](#query-parameters)
- [Navigation](#navigation)
- [Protected Routes](#protected-routes)
- [Forms](#forms)

## Setup

Add `leptos_router` to dependencies (same version as `leptos`):

```toml
[dependencies]
leptos_router = { version = "0.8", features = ["csr"] }  # or ssr/hydrate
```

Basic router structure:

```rust
use leptos::prelude::*;
use leptos_router::{
    components::{Router, Routes, Route, A, Outlet},
    path,
};

#[component]
pub fn App() -> impl IntoView {
    view! {
        <Router>
            <nav>
                <A href="/">"Home"</A>
                <A href="/about">"About"</A>
            </nav>
            <main>
                <Routes fallback=|| "Page not found">
                    <Route path=path!("/") view=Home />
                    <Route path=path!("/about") view=About />
                </Routes>
            </main>
        </Router>
    }
}
```

## Route Definition

Use `path!` macro for type-safe paths:

```rust
<Route path=path!("/") view=Home />
<Route path=path!("/users") view=UserList />
<Route path=path!("/users/:id") view=UserDetail />
<Route path=path!("/files/*path") view=FileViewer />  // catch-all
```

Path patterns:
- `/static` - exact match
- `/:param` - named parameter
- `/*rest` - catch-all (captures remaining path)

## Nested Routes

Use `<ParentRoute>` with `<Outlet/>` for nested layouts:

```rust
use leptos_router::components::{ParentRoute, Outlet};

#[component]
pub fn App() -> impl IntoView {
    view! {
        <Router>
            <Routes fallback=|| "Not found">
                <ParentRoute path=path!("/dashboard") view=DashboardLayout>
                    <Route path=path!("/") view=DashboardHome />
                    <Route path=path!("/settings") view=DashboardSettings />
                    <Route path=path!("/users/:id") view=UserDetail />
                </ParentRoute>
            </Routes>
        </Router>
    }
}

#[component]
fn DashboardLayout() -> impl IntoView {
    view! {
        <div class="dashboard">
            <aside>"Sidebar"</aside>
            <main>
                <Outlet/>  // Child route renders here
            </main>
        </div>
    }
}
```

For transparent route grouping (no wrapper component):

```rust
#[component(transparent)]
pub fn UserRoutes() -> impl MatchNestedRoutes + Clone {
    view! {
        <ParentRoute path=path!("/users") view=UserLayout>
            <Route path=path!("/") view=UserList />
            <Route path=path!("/:id") view=UserDetail />
        </ParentRoute>
    }
    .into_inner()
}

// Use in main routes:
<Routes fallback=|| "Not found">
    <Route path=path!("/") view=Home />
    <UserRoutes />
</Routes>
```

## Route Parameters

### Defining Params

Use `Params` derive macro:

```rust
use leptos_router::params::Params;

#[derive(Params, PartialEq, Clone, Debug)]
pub struct UserParams {
    id: Option<usize>,  // Option for safety
}

#[derive(Params, PartialEq, Clone, Debug)]
pub struct FileParams {
    path: Option<String>,  // catch-all parameter
}
```

### Reading Params

Use `use_params()` hook:

```rust
use leptos_router::hooks::use_params;

#[component]
fn UserDetail() -> impl IntoView {
    let params = use_params::<UserParams>();

    // Reactive - updates when URL changes
    let user_id = move || {
        params.get()
            .ok()
            .and_then(|p| p.id)
    };

    view! {
        <div>
            "User ID: " {user_id}
        </div>
    }
}
```

With async data loading:

```rust
#[component]
fn UserDetail() -> impl IntoView {
    let params = use_params::<UserParams>();

    let user = AsyncDerived::new(move || {
        let id = params.get().ok().and_then(|p| p.id);
        async move {
            match id {
                Some(id) => fetch_user(id).await.ok(),
                None => None,
            }
        }
    });

    view! {
        <Suspense fallback=|| "Loading...">
            {move || Suspend::new(async move {
                user.await.map(|u| view! { <p>{u.name}</p> })
            })}
        </Suspense>
    }
}
```

## Query Parameters

Use `use_query_map()` for query string access:

```rust
use leptos_router::hooks::use_query_map;

#[component]
fn SearchPage() -> impl IntoView {
    let query = use_query_map();

    // Reactive memo for specific param
    let search_term = Memo::new(move |_| {
        query.read().get("q").unwrap_or_default()
    });

    let page = Memo::new(move |_| {
        query.read()
            .get("page")
            .and_then(|p| p.parse::<usize>().ok())
            .unwrap_or(1)
    });

    view! {
        <div>
            "Search: " {search_term}
            " Page: " {page}
        </div>
    }
}
```

## Navigation

### Link Component

Use `<A>` for client-side navigation:

```rust
use leptos_router::components::A;

view! {
    <A href="/users/42">"View User"</A>
    <A href="/search?q=rust">"Search Rust"</A>

    // External links (bypasses router)
    <a href="https://example.com" target="_blank">"External"</a>
}
```

`<A>` benefits:
- Prevents full page reload
- Prefetches on hover (configurable)
- Works before WASM loads (progressive enhancement)

### Programmatic Navigation

Use `use_navigate()` hook:

```rust
use leptos_router::hooks::use_navigate;

#[component]
fn LoginForm() -> impl IntoView {
    let navigate = use_navigate();

    let on_success = move || {
        // Navigate after successful login
        navigate("/dashboard", Default::default());
    };

    view! {
        <button on:click=move |_| on_success()>
            "Login"
        </button>
    }
}
```

Navigation options:

```rust
use leptos_router::NavigateOptions;

// Replace history entry (no back button)
navigate("/new-path", NavigateOptions {
    replace: true,
    ..Default::default()
});

// Preserve scroll position
navigate("/same-page", NavigateOptions {
    scroll: false,
    ..Default::default()
});
```

### Location Info

Access current location:

```rust
use leptos_router::hooks::use_location;

#[component]
fn CurrentPath() -> impl IntoView {
    let location = use_location();

    view! {
        <p>"Current path: " {move || location.pathname.get()}</p>
        <p>"Query: " {move || location.search.get()}</p>
        <p>"Hash: " {move || location.hash.get()}</p>
    }
}
```

## Protected Routes

Use `<ProtectedRoute>` for auth-guarded routes:

```rust
use leptos_router::components::ProtectedRoute;

#[component]
fn App() -> impl IntoView {
    let logged_in = RwSignal::new(false);

    view! {
        <Router>
            <Routes fallback=|| "Not found">
                <Route path=path!("/") view=Home />
                <Route path=path!("/login") view=Login />
                <ProtectedRoute
                    path=path!("/dashboard")
                    condition=move || Some(logged_in.get())
                    redirect_path=|| "/login"
                    view=Dashboard
                />
            </Routes>
        </Router>
    }
}
```

`condition` returns `Option<bool>`:
- `Some(true)` - allow access
- `Some(false)` - redirect
- `None` - show loading (condition pending)

## Forms

### Form Component

Use `<Form>` for client-side form handling with progressive enhancement:

```rust
use leptos_router::components::Form;

#[component]
fn SearchForm() -> impl IntoView {
    view! {
        // GET form - updates URL, triggers navigation
        <Form method="GET" action="/search">
            <input type="text" name="q" />
            <button type="submit">"Search"</button>
        </Form>
    }
}
```

### ActionForm for Server Functions

Use `<ActionForm>` with server actions:

```rust
use leptos::prelude::*;
use leptos_router::components::ActionForm;

#[server]
async fn add_todo(title: String) -> Result<(), ServerFnError> {
    // Server-side logic
    Ok(())
}

#[component]
fn TodoForm() -> impl IntoView {
    let add_todo = ServerAction::<AddTodo>::new();

    view! {
        <ActionForm action=add_todo>
            <input type="text" name="title" />
            <button type="submit">"Add Todo"</button>
        </ActionForm>

        // Show loading state
        <Show when=move || add_todo.pending().get()>
            "Saving..."
        </Show>
    }
}
```

Form callbacks for custom handling:

```rust
<Form
    method="POST"
    action="/api/submit"
    on_form_data=|form_data| {
        // Modify form data before submit
    }
    on_response=|response| {
        // Handle response
    }
    on_error=|error| {
        // Handle errors
    }
>
```

## Transitions

Enable smooth transitions between routes:

```rust
<Routes transition=true fallback=|| "Not found">
    // Routes...
</Routes>
```

Track transition state:

```rust
let (is_routing, set_is_routing) = signal(false);

view! {
    <Router set_is_routing>
        <Show when=move || is_routing.get()>
            <div class="loading-bar" />
        </Show>
        // ...
    </Router>
}
```
