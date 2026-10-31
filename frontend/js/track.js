/* Site analytics (#165): one track(name, props) helper for every event, so the tool
   can be swapped later. PostHog (US cloud, D21): cookieless (persistence 'memory'),
   page views and the named events only. No session replay, no autocapture.
   Event names and properties: docs/ANALYTICS.md (a test checks every name).

   - Loaded on every page from the shared snippet (scripts/site_analytics.py), after
     PostHog's script; a stub in the snippet queues calls made before this runs.
   - Never throws, and never stops the page: if PostHog is blocked, track() does nothing.
   - On localhost nothing is sent; events are logged to the console instead.
   - Also sends the events every page shares: menu_click, outbound_click,
     see_all_click, and section_view on the home page. */
(() => {
    const KEY = 'phc_CqZ9BEFt4bipAkskFUnhBua3DtFmT3jgDyEgw6tw5EYw';   // public by design
    const LOCAL = /^(localhost|127\.0\.0\.1|\[::1\])$/.test(location.hostname);
    const queued = Array.isArray(window.__trackQ) ? window.__trackQ : [];
    let ph = null;

    try {
        if (!LOCAL && window.posthog && typeof window.posthog.init === 'function') {
            window.posthog.init(KEY, {
                api_host: 'https://us.i.posthog.com',
                persistence: 'memory',               // no cookies, no local or session storage
                person_profiles: 'identified_only',  // we never identify anyone
                respect_dnt: true,
                capture_pageview: true,
                autocapture: false,                  // only the named events
                disable_session_recording: true,
                capture_pageleave: false,
                capture_heatmaps: false,
                rageclick: false,
                capture_dead_clicks: false,
                capture_performance: false,
                capture_exceptions: false,
                disable_surveys: true,
                disable_web_experiments: true,
                disable_product_tours: true,
                disable_conversations: true,
                advanced_disable_flags: true,        // no feature flags
            });
            ph = window.posthog;
        }
    } catch (e) { ph = null; }

    // opts.beacon: send even while the page is closing (gameday_view)
    function track(name, props, opts) {
        try {
            if (LOCAL) { console.debug('[track]', name, props || {}); return; }
            if (ph) ph.capture(name, props || {}, opts && opts.beacon ? { transport: 'sendBeacon' } : undefined);
        } catch (e) { /* analytics never breaks the page */ }
    }
    window.track = track;
    queued.forEach(([n, p, o]) => track(n, p, o));
    queued.length = 0;

    // ---- events every page shares ------------------------------------------------

    const textOnly = el => [...el.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent).join('').trim();

    document.addEventListener('click', (e) => {
        const a = e.target instanceof Element ? e.target.closest('a[href]') : null;
        if (!a) return;
        if (a.closest('.site-nav .nav-links')) {
            track('menu_click', { label: textOnly(a), from: location.pathname });
            return;
        }
        if (a.closest('.see-all')) {
            track('see_all_click', { section: a.closest('section[id]')?.id || '' });
            return;
        }
        let url;
        try { url = new URL(a.href, location.href); } catch (err) { return; }
        if (!/^https?:$/.test(url.protocol) || url.host === location.host) return;
        const host = url.hostname.replace(/^www\./, '');
        const destination = /^(x|twitter)\.com$/.test(host) ? 'x' : /(^|\.)reddit\.com$/.test(host) ? 'reddit' : 'other';
        track('outbound_click', { destination });
    }, true);

    // Home sections: once per page view, when half the section or half the screen shows
    // (a section taller than two screens can never be half visible on a phone)
    if (location.pathname === '/' && 'IntersectionObserver' in window) {
        const seen = new Set();
        const io = new IntersectionObserver((entries) => {
            entries.forEach((en) => {
                const id = en.target.id;
                if (seen.has(id) || !en.isIntersecting) return;
                if (en.intersectionRatio >= 0.5 || en.intersectionRect.height >= 0.5 * window.innerHeight) {
                    seen.add(id);
                    io.unobserve(en.target);
                    track('section_view', { section: id });
                }
            });
        }, { threshold: [0, 0.05, 0.1, 0.25, 0.5, 0.75, 1] });
        document.querySelectorAll('section[id]').forEach(s => io.observe(s));
    }
})();
