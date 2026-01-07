# Server Functions Reference

## Table of Contents
- [Overview](#overview)
- [Basic Usage](#basic-usage)
- [Encodings](#encodings)
- [Actions](#actions)
- [Resources](#resources)
- [AsyncDerived](#asyncderived)
- [SSR and Hydration](#ssr-and-hydration)
- [Server Integrations](#server-integrations)

## Overview

Server functions are RPC endpoints that:
- Define logic on the server
- Generate client-callable functions automatically
- Use web standards (POST/GET with URL-encoded data)
- Support graceful degradation (work without JS)

## Basic Usage

### Defining Server Functions

```rust
use leptos::prelude::*;
use server_fn::ServerFnError;

#[server]
pub async fn get_user(id: u64) -> Result<User, ServerFnError> {
    // This code only runs on the server
    let user = db::fetch_user(id).await?;
    Ok(user)
}

#[server]
pub async fn save_settings(
    theme: String,
    notifications: bool,
) -> Result<(), ServerFnError> {
    // Multiple arguments supported
    db::update_settings(theme, notifications).await?;
    Ok(())
}
```

### Calling Server Functions

From client code:

```rust
// Direct call (returns Future)
let user = get_user(42).await;

// With action (for mutations)
let save = ServerAction::<SaveSettings>::new();
save.dispatch(SaveSettings { theme: "dark".into(), notifications: true });

// With resource (for data loading)
let user = Resource::new(|| (), |_| get_user(42));
```

### Error Handling

Server functions return `Result<T, ServerFnError>`:

```rust
#[server]
pub async fn risky_operation() -> Result<Data, ServerFnError> {
    // Convert errors with ?
    let data = external_api().await
        .map_err(|e| ServerFnError::ServerError(e.to_string()))?;

    // Or create errors directly
    if !valid {
        return Err(ServerFnError::ServerError("Invalid data".into()));
    }

    Ok(data)
}
```

Common error types:
- `ServerFnError::ServerError(String)` - general server error
- `ServerFnError::Deserialization(String)` - parsing error
- `ServerFnError::Serialization(String)` - encoding error
- `ServerFnError::Request(String)` - network error

## Encodings

### Input Encodings

Default is `PostUrl` (URL-encoded POST):

```rust
#[server]  // Default: PostUrl input
pub async fn default_fn(data: String) -> Result<(), ServerFnError> { }

#[server(input = GetUrl)]  // GET with query params
pub async fn get_fn(id: u64) -> Result<Data, ServerFnError> { }

#[server(input = Json)]  // JSON POST body
pub async fn json_fn(data: ComplexStruct) -> Result<(), ServerFnError> { }

#[server(input = MultipartFormData)]  // File uploads
pub async fn upload_fn(file: MultipartData) -> Result<(), ServerFnError> { }
```

### Output Encodings

Default is `Json`:

```rust
#[server(output = Json)]  // Default
pub async fn json_output() -> Result<Data, ServerFnError> { }

#[server(output = StreamingText)]  // Text streaming
pub async fn stream_text() -> Result<TextStream, ServerFnError> { }

#[server(output = Streaming)]  // Binary streaming
pub async fn stream_bytes() -> Result<ByteStream, ServerFnError> { }
```

### Custom Endpoints

Override the default path:

```rust
#[server(endpoint = "/api/v2/users")]
pub async fn get_users() -> Result<Vec<User>, ServerFnError> { }
```

## Actions

### ServerAction

For mutations (POST operations):

```rust
use leptos::prelude::*;

#[server]
pub async fn add_todo(title: String) -> Result<Todo, ServerFnError> {
    db::insert_todo(title).await
}

#[component]
fn TodoForm() -> impl IntoView {
    let add_todo = ServerAction::<AddTodo>::new();

    // Reactive state
    let pending = add_todo.pending();      // Signal<bool>
    let value = add_todo.value();          // Signal<Option<Result<Todo, _>>>
    let input = add_todo.input();          // Signal<Option<AddTodo>>

    view! {
        <form on:submit=move |ev| {
            ev.prevent_default();
            add_todo.dispatch(AddTodo { title: "New".into() });
        }>
            <input type="text" name="title" />
            <button type="submit" disabled=move || pending.get()>
                {move || if pending.get() { "Saving..." } else { "Add" }}
            </button>
        </form>

        // Show result
        {move || value.get().map(|result| match result {
            Ok(todo) => view! { <p>"Added: " {todo.title}</p> }.into_any(),
            Err(e) => view! { <p class="error">{e.to_string()}</p> }.into_any(),
        })}
    }
}
```

### ServerMultiAction

For multiple concurrent calls:

```rust
let multi = ServerMultiAction::<AddTodo>::new();

// Each dispatch creates a separate submission
multi.dispatch(AddTodo { title: "First".into() });
multi.dispatch(AddTodo { title: "Second".into() });

// Track all submissions
let submissions = multi.submissions();  // Vec<Submission>
```

### ActionForm Integration

For progressive enhancement:

```rust
use leptos_router::components::ActionForm;

#[component]
fn TodoForm() -> impl IntoView {
    let add_todo = ServerAction::<AddTodo>::new();

    view! {
        // Works even without JS!
        <ActionForm action=add_todo>
            <input type="text" name="title" />
            <button type="submit">"Add"</button>
        </ActionForm>
    }
}
```

## Resources

### Resource (for SSR)

Loads data on server, serializes for client:

```rust
use leptos::prelude::*;

#[component]
fn UserProfile() -> impl IntoView {
    let user_id = RwSignal::new(1u64);

    // Re-fetches when user_id changes
    let user = Resource::new(
        move || user_id.get(),
        |id| get_user(id)
    );

    view! {
        <Suspense fallback=|| "Loading...">
            {move || Suspend::new(async move {
                user.await.map(|u| view! {
                    <div>
                        <h1>{u.name}</h1>
                        <p>{u.email}</p>
                    </div>
                })
            })}
        </Suspense>
    }
}
```

### LocalResource (CSR only)

For client-only data loading:

```rust
// Does not run on server, no serialization
let local_data = LocalResource::new(move || {
    fetch_from_browser_api()
});
```

### Resource Methods

```rust
let resource = Resource::new(|| (), |_| fetch_data());

// Read current value (Option<T>)
let current = resource.get();

// Refetch manually
resource.refetch();

// Check loading state (deprecated, use Suspense)
let loading = resource.loading();
```

## AsyncDerived

For async computed values:

```rust
use leptos::prelude::*;

#[component]
fn SearchResults() -> impl IntoView {
    let query = RwSignal::new(String::new());

    // Async derived value - recomputes when query changes
    let results = AsyncDerived::new(move || {
        let q = query.get();
        async move {
            if q.is_empty() {
                vec![]
            } else {
                search_api(q).await.unwrap_or_default()
            }
        }
    });

    view! {
        <input
            prop:value=query
            on:input:target=move |ev| query.set(ev.target().value())
        />

        <Suspense fallback=|| "Searching...">
            {move || Suspend::new(async move {
                let items = results.await;
                view! {
                    <ul>
                        {items.into_iter().map(|item| view! {
                            <li>{item.title}</li>
                        }).collect_view()}
                    </ul>
                }
            })}
        </Suspense>
    }
}
```

## SSR and Hydration

### Feature Flags

```toml
[features]
ssr = ["leptos/ssr", "leptos_router/ssr"]
hydrate = ["leptos/hydrate", "leptos_router/hydrate"]
```

### Server-Only Code

```rust
#[server]
pub async fn server_only() -> Result<(), ServerFnError> {
    // Code here only compiles/runs on server

    // Access server-specific APIs
    #[cfg(feature = "ssr")]
    {
        use tokio::fs;
        let data = fs::read("secret.txt").await?;
    }

    Ok(())
}
```

### SharedValue

Share values between SSR and hydration without refetch:

```rust
use leptos_server::SharedValue;

#[component]
fn App() -> impl IntoView {
    // Computed on server, hydrated on client
    let config = SharedValue::new(|| {
        load_config()  // Only runs on server
    });

    view! {
        <p>"Config: " {config.get().name}</p>
    }
}
```

### Streaming SSR

Out-of-order streaming (default):
- Shell renders immediately
- Suspense fallbacks show first
- Content streams in as resources resolve

In-order streaming:
- Content renders in DOM order
- Better for SEO in some cases

Configure in server integration.

## Server Integrations

### Axum

```rust
use axum::{routing::get, Router};
use leptos_axum::{generate_route_list, LeptosRoutes};

#[tokio::main]
async fn main() {
    let conf = get_configuration(None).unwrap();
    let routes = generate_route_list(App);

    let app = Router::new()
        .leptos_routes(&conf.leptos_options, routes, App)
        .fallback(file_and_error_handler);

    // Server functions registered automatically
    axum::serve(listener, app).await.unwrap();
}
```

### Actix

```rust
use actix_web::{App, HttpServer};
use leptos_actix::{generate_route_list, LeptosRoutes};

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    let conf = get_configuration(None).unwrap();
    let routes = generate_route_list(App);

    HttpServer::new(move || {
        App::new()
            .leptos_routes(routes.clone(), App)
    })
    .bind(("127.0.0.1", 3000))?
    .run()
    .await
}
```

### Response Headers

Set headers/status from server functions:

```rust
use leptos_axum::ResponseOptions;  // or leptos_actix

#[server]
pub async fn custom_response() -> Result<(), ServerFnError> {
    let response = expect_context::<ResponseOptions>();

    // Set status code
    response.set_status(StatusCode::CREATED);

    // Set headers
    response.insert_header(
        HeaderName::from_static("x-custom"),
        HeaderValue::from_static("value")
    );

    Ok(())
}
```

### Redirects

```rust
use leptos_axum::redirect;  // or leptos_actix

#[server]
pub async fn login(creds: Credentials) -> Result<(), ServerFnError> {
    if authenticate(creds).await? {
        redirect("/dashboard");
    }
    Ok(())
}
```
