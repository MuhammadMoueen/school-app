(function () {
    function parseConfig() {
        var el = document.getElementById('studentDashboardConfig');
        if (!el) return null;
        try {
            return JSON.parse(el.textContent || '{}');
        } catch (err) {
            console.error('Invalid student dashboard config', err);
            return null;
        }
    }

    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i += 1) {
                var cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    function StudentSmartDashboard(root, config) {
        this.root = root;
        this.config = config || {};
        this.sectionUrlTemplate = root.dataset.sectionUrlTemplate || '';
        this.contentContainer = document.getElementById('dashboard-content');
        this.navLinks = Array.prototype.slice.call(document.querySelectorAll('.js-dashboard-nav[data-dashboard-section]'));
        this.analytics = (this.config && this.config.analytics) || {};
        this.currentSection = (this.config && this.config.initialSection) || 'dashboard';
        this.chartInstances = {};
        this.csrfToken = getCookie('csrftoken');
        this.sectionCache = {};
    }

    StudentSmartDashboard.prototype.init = function () {
        if (!this.contentContainer) return;

        this.bindNav();
        this.syncNavState(this.currentSection);
        this.renderCharts(this.currentSection, this.analytics);
        this.sectionCache[this.currentSection] = {
            html: this.contentContainer.innerHTML,
            analytics: this.analytics || {}
        };

        var self = this;
        window.addEventListener('popstate', function () {
            var section = self.readSectionFromUrl() || 'dashboard';
            self.loadSection(section, false);
        });
    };

    StudentSmartDashboard.prototype.bindNav = function () {
        var self = this;
        this.navLinks.forEach(function (link) {
            link.addEventListener('click', function (event) {
                if (!self.contentContainer) return;
                event.preventDefault();
                var section = link.dataset.dashboardSection || 'dashboard';
                self.loadSection(section, true);
            });
        });
    };

    StudentSmartDashboard.prototype.readSectionFromUrl = function () {
        try {
            var url = new URL(window.location.href);
            return url.searchParams.get('section');
        } catch (err) {
            return null;
        }
    };

    StudentSmartDashboard.prototype.syncNavState = function (section) {
        this.navLinks.forEach(function (link) {
            link.classList.toggle('active', link.dataset.dashboardSection === section);
        });
    };

    StudentSmartDashboard.prototype.setLoading = function () {
        this.contentContainer.innerHTML = '<div class="smart-card loading-card"><i class="fas fa-spinner fa-spin"></i><p>Loading analytics section...</p></div>';
    };

    StudentSmartDashboard.prototype.scrollToContentTop = function () {
        var topbar = document.querySelector('.teacher-topbar');
        var offset = topbar ? (topbar.offsetHeight + 16) : 0;
        var top = this.contentContainer.getBoundingClientRect().top + window.scrollY - offset;
        window.scrollTo({ top: Math.max(0, top), behavior: 'auto' });
    };

    StudentSmartDashboard.prototype.getSectionUrl = function (section) {
        return this.sectionUrlTemplate.replace('__SECTION__', section);
    };

    StudentSmartDashboard.prototype.loadSection = function (section, pushState) {
        var self = this;

        this.scrollToContentTop();

        if (this.sectionCache[section]) {
            this.currentSection = section;
            this.analytics = this.sectionCache[section].analytics || {};
            this.contentContainer.innerHTML = this.sectionCache[section].html || '';
            this.syncNavState(this.currentSection);
            this.renderCharts(this.currentSection, this.analytics);

            if (pushState) {
                var cachedUrl = new URL(window.location.href);
                cachedUrl.searchParams.set('section', this.currentSection);
                window.history.pushState({ section: this.currentSection }, '', cachedUrl.toString());
            }
            return;
        }

        var url = this.getSectionUrl(section);
        var requestUrl = new URL(url, window.location.origin);
        requestUrl.searchParams.set('_ts', Date.now().toString());

        this.setLoading();
        this.syncNavState(section);

        fetch(requestUrl.toString(), {
            method: 'GET',
            cache: 'no-store',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': this.csrfToken || ''
            }
        })
            .then(function (response) { return response.json(); })
            .then(function (data) {
                if (!data || !data.success) {
                    throw new Error((data && data.error) || 'Failed to load section');
                }

                self.currentSection = data.section;
                self.analytics = data.analytics || {};
                self.contentContainer.innerHTML = data.html || '';
                self.sectionCache[self.currentSection] = {
                    html: self.contentContainer.innerHTML,
                    analytics: self.analytics
                };
                self.syncNavState(self.currentSection);
                self.renderCharts(self.currentSection, self.analytics);

                if (pushState) {
                    var newUrl = new URL(window.location.href);
                    newUrl.searchParams.set('section', self.currentSection);
                    window.history.pushState({ section: self.currentSection }, '', newUrl.toString());
                }
            })
            .catch(function (err) {
                console.error('Section load error:', err);
                self.contentContainer.innerHTML = '<div class="smart-card loading-card error"><i class="fas fa-exclamation-triangle"></i><p>Unable to load this section right now.</p></div>';
            });
    };

    StudentSmartDashboard.prototype.destroyCharts = function () {
        var keys = Object.keys(this.chartInstances);
        for (var i = 0; i < keys.length; i += 1) {
            var instance = this.chartInstances[keys[i]];
            if (instance && typeof instance.destroy === 'function') {
                instance.destroy();
            }
        }
        this.chartInstances = {};
    };

    StudentSmartDashboard.prototype.makeChart = function (id, config) {
        var canvas = document.getElementById(id);
        if (!canvas || typeof Chart === 'undefined') return;
        this.chartInstances[id] = new Chart(canvas, config);
    };

    StudentSmartDashboard.prototype.renderCharts = function (section, analytics) {
        this.destroyCharts();
        if (typeof Chart === 'undefined') return;

        var theme = {
            primary: '#5b6ee1',
            purple: '#6f42c1',
            cyan: '#1fb6ff',
            green: '#2fbf71',
            orange: '#f59f00',
            red: '#ef4444',
            muted: '#94a3b8'
        };

        if (section === 'dashboard') {
            this.makeChart('performanceTrendChart', {
                type: 'line',
                data: {
                    labels: (analytics.performance_chart && analytics.performance_chart.labels) || [],
                    datasets: [{
                        label: 'Marks %',
                        data: (analytics.performance_chart && analytics.performance_chart.marks) || [],
                        borderColor: theme.primary,
                        backgroundColor: 'rgba(91, 110, 225, 0.15)',
                        borderWidth: 3,
                        fill: true,
                        tension: 0.35,
                        pointRadius: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: { beginAtZero: true, max: 100 }
                    }
                }
            });

            this.makeChart('attendanceDonutChart', {
                type: 'doughnut',
                data: {
                    labels: (analytics.attendance_chart && analytics.attendance_chart.labels) || [],
                    datasets: [{
                        data: (analytics.attendance_chart && analytics.attendance_chart.values) || [],
                        backgroundColor: [theme.green, theme.red, theme.orange, theme.cyan]
                    }]
                },
                options: { responsive: true, maintainAspectRatio: false }
            });

            this.makeChart('assignmentBarChart', {
                type: 'bar',
                data: {
                    labels: (analytics.assignment_progress && analytics.assignment_progress.labels) || [],
                    datasets: [{
                        label: 'Assignments',
                        data: (analytics.assignment_progress && analytics.assignment_progress.values) || [],
                        backgroundColor: [theme.green, theme.orange, theme.red],
                        borderRadius: 8
                    }]
                },
                options: { responsive: true, maintainAspectRatio: false }
            });

            this.makeChart('quizGaugeChart', {
                type: 'doughnut',
                data: {
                    labels: ['Attempted', 'Not Attempted'],
                    datasets: [{
                        data: [
                            (analytics.quiz_performance && analytics.quiz_performance.attempted) || 0,
                            (analytics.quiz_performance && analytics.quiz_performance.not_attempted) || 0
                        ],
                        backgroundColor: [theme.purple, theme.muted]
                    }]
                },
                options: { responsive: true, maintainAspectRatio: false }
            });
        }

        if (section === 'assignments') {
            this.makeChart('assignmentSectionChart', {
                type: 'bar',
                data: {
                    labels: (analytics.assignment_progress && analytics.assignment_progress.labels) || [],
                    datasets: [{
                        label: 'Assignment Status',
                        data: (analytics.assignment_progress && analytics.assignment_progress.values) || [],
                        backgroundColor: [theme.green, theme.orange, theme.red],
                        borderRadius: 10
                    }]
                },
                options: { responsive: true, maintainAspectRatio: false }
            });
        }

        if (section === 'quizzes') {
            this.makeChart('quizSectionChart', {
                type: 'doughnut',
                data: {
                    labels: ['Attempted', 'Not Attempted'],
                    datasets: [{
                        data: [
                            (analytics.quiz_performance && analytics.quiz_performance.attempted) || 0,
                            (analytics.quiz_performance && analytics.quiz_performance.not_attempted) || 0
                        ],
                        backgroundColor: [theme.primary, theme.muted]
                    }]
                },
                options: { responsive: true, maintainAspectRatio: false }
            });
        }

        if (section === 'attendance') {
            this.makeChart('attendanceSectionChart', {
                type: 'pie',
                data: {
                    labels: (analytics.attendance_chart && analytics.attendance_chart.labels) || [],
                    datasets: [{
                        data: (analytics.attendance_chart && analytics.attendance_chart.values) || [],
                        backgroundColor: [theme.green, theme.red, theme.orange, theme.cyan]
                    }]
                },
                options: { responsive: true, maintainAspectRatio: false }
            });
        }

        if (section === 'reports') {
            this.makeChart('reportSectionChart', {
                type: 'bar',
                data: {
                    labels: (analytics.report_summary && analytics.report_summary.labels) || [],
                    datasets: [{
                        label: 'Report Threads',
                        data: (analytics.report_summary && analytics.report_summary.values) || [],
                        backgroundColor: [theme.orange, theme.cyan, theme.green],
                        borderRadius: 10
                    }]
                },
                options: { responsive: true, maintainAspectRatio: false }
            });
        }
    };

    document.addEventListener('DOMContentLoaded', function () {
        var root = document.getElementById('studentSmartDashboard');
        var config = parseConfig();
        if (!root || !config) return;
        var dashboard = new StudentSmartDashboard(root, config);
        dashboard.init();
    });
})();
