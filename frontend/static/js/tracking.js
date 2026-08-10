// Behavioral Event Tracking System
class EventTracker {
    constructor() {
        this.eventQueue = [];
        this.batchSize = 10;
        this.flushInterval = 5000; // 5 seconds
        this.isFlushing = false;
        this.sessionId = this.generateSessionId();
        this.trackedViews = new Set();
        this.lastScrollTime = 0;
        this.scrollDepth = 0;
        
        // Start periodic flush
        setInterval(() => this.flush(), this.flushInterval);
        
        // Setup page unload handler
        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'hidden') {
                this.flush();
            }
        });
        
        // Track page leave
        window.addEventListener('beforeunload', () => {
            this.flush();
        });
    }
    
    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substring(2, 9);
    }
    
    trackEvent(eventType, productId = null, productTitle = null, metadata = {}) {
        const event = {
            event_type: eventType,
            product_id: productId,
            product_title: productTitle,
            session_id: this.sessionId,
            timestamp: new Date().toISOString(),
            url: window.location.href,
            user_agent: navigator.userAgent,
            metadata: metadata,
            ...metadata
        };
        
        // Add to queue
        this.eventQueue.push(event);
        
        // Flush if queue is full
        if (this.eventQueue.length >= this.batchSize) {
            this.flush();
        }
        
        // For debugging
        if (process.env.NODE_ENV === 'development') {
            console.log('Event tracked:', event);
        }
        
        return event;
    }
    
    flush() {
        if (this.isFlushing || this.eventQueue.length === 0) {
            return;
        }
        
        this.isFlushing = true;
        const events = [...this.eventQueue];
        this.eventQueue = [];
        
        // Send events
        fetch('/api/track-events', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ events: events }),
            keepalive: true
        })
        .then(response => {
            if (!response.ok) {
                // Put events back in queue on failure
                this.eventQueue = [...events, ...this.eventQueue];
            }
        })
        .catch(error => {
            // Put events back in queue on error
            this.eventQueue = [...events, ...this.eventQueue];
            console.error('Error sending events:', error);
        })
        .finally(() => {
            this.isFlushing = false;
        });
    }
    
    // Specialized tracking methods
    trackView(productId, productTitle) {
        const key = productId + '_' + this.sessionId;
        if (!this.trackedViews.has(key)) {
            this.trackEvent('view', productId, productTitle);
            this.trackedViews.add(key);
        }
    }
    
    trackSearch(query, results = null) {
        this.trackEvent('search', null, null, { 
            query: query,
            results_count: results ? results.length : 0
        });
    }
    
    trackClick(productId, productTitle, location = 'list') {
        this.trackEvent('click', productId, productTitle, { location: location });
    }
    
    trackTimeSpent(productId, productTitle, seconds) {
        if (seconds >= 5) { // Only track if significant time
            this.trackEvent('time_spent', productId, productTitle, { seconds: seconds });
        }
    }
    
    trackScrollDepth(depth) {
        // Only track if depth increased significantly
        if (depth > this.scrollDepth + 10) {
            this.scrollDepth = depth;
            this.trackEvent('scroll', null, null, { depth: depth });
        }
    }
    
    trackExitIntent() {
        this.trackEvent('exit_intent');
    }
}

// Initialize tracker
const tracker = new EventTracker();

// Make tracker globally available
window.tracker = tracker;

// Convenience function
function trackEvent(eventType, productId = null, productTitle = null, metadata = {}) {
    return tracker.trackEvent(eventType, productId, productTitle, metadata);
}

// Auto-track page view
document.addEventListener('DOMContentLoaded', function() {
    // Track page view with page title
    tracker.trackEvent('page_view', null, null, {
        page_title: document.title,
        page_path: window.location.pathname
    });
});

// Track exit intent
document.addEventListener('mouseleave', function(e) {
    if (e.clientY < 0) {
        tracker.trackExitIntent();
    }
});

// Track scroll depth
document.addEventListener('scroll', function() {
    const scrollTop = window.scrollY;
    const docHeight = document.documentElement.scrollHeight - window.innerHeight;
    const depth = Math.round((scrollTop / docHeight) * 100);
    tracker.trackScrollDepth(depth);
});

// Track time on page
let pageLoadTime = Date.now();
window.addEventListener('beforeunload', function() {
    const timeSpent = Math.floor((Date.now() - pageLoadTime) / 1000);
    if (timeSpent > 10) {
        tracker.trackEvent('page_time', null, null, { seconds: timeSpent });
    }
});