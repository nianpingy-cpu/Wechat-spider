export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const backend = env.BACKEND_URL || "https://wechat-spider.onrender.com";
    const targetUrl = backend + url.pathname + url.search;

    // CORS 预检请求直接返回
    if (request.method === "OPTIONS") {
      return new Response(null, {
        status: 204,
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
          "Access-Control-Allow-Headers": "*",
          "Access-Control-Max-Age": "86400",
        },
      });
    }

    try {
      // 先快速唤醒 Render（仅发 HEAD，不阻塞）
      const wakeUrl = backend + "/";
      fetch(wakeUrl, { method: "HEAD" }).catch(() => {});

      // 代理请求，最多重试 3 次（等 Render 唤醒）
      let response;
      let lastError;
      for (let i = 0; i < 3; i++) {
        try {
          const body = request.method !== "GET" && request.method !== "HEAD"
            ? await request.clone().text()
            : null;

          response = await fetch(targetUrl, {
            method: request.method,
            headers: request.headers,
            body: body,
          });

          if (response.ok || response.status >= 400) break;

          // 如果后端还在启动，等 8 秒重试
          if (i < 2) await new Promise(r => setTimeout(r, 8000));
        } catch (e) {
          lastError = e;
          if (i < 2) await new Promise(r => setTimeout(r, 8000));
        }
      }

      if (!response) {
        return new Response(JSON.stringify({
          detail: "后端正在启动，请 30 秒后重试",
        }), {
          status: 503,
          headers: {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
          },
        });
      }

      const newHeaders = new Headers(response.headers);
      newHeaders.set("Access-Control-Allow-Origin", "*");
      if (!newHeaders.has("Access-Control-Allow-Methods")) {
        newHeaders.set("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE,OPTIONS");
      }
      if (!newHeaders.has("Access-Control-Allow-Headers")) {
        newHeaders.set("Access-Control-Allow-Headers", "*");
      }

      return new Response(response.body, {
        status: response.status,
        statusText: response.statusText,
        headers: newHeaders,
      });

    } catch (e) {
      return new Response(JSON.stringify({
        detail: "网络错误，请稍后重试",
      }), {
        status: 502,
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*",
        },
      });
    }
  },
};
