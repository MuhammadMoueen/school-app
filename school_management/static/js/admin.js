/* ========================================
   ADMIN PANEL - CONSOLIDATED JAVASCRIPT
   THE CITY SCHOOL OF BAHAWALPUR
   ======================================== */

/**
 * Admin Dashboard - Global Search Functionality
 * Handles real-time search for students and teachers
 */
const AdminDashboard = {
    init: function() {
        const searchInput = document.getElementById('globalSearch');
        const searchResults = document.getElementById('searchResults');
        
        if (!searchInput || !searchResults) {
            return; // Not on dashboard page
        }

        let searchTimeout = null;

        searchInput.addEventListener('input', function() {
            const query = this.value.trim();
            clearTimeout(searchTimeout);

            if (query.length < 2) {
                searchResults.classList.remove('active');
                searchResults.innerHTML = '';
                return;
            }

            searchResults.innerHTML = '<div class="search-loading"><i class="fas fa-spinner fa-spin"></i> Searching...</div>';
            searchResults.classList.add('active');

            searchTimeout = setTimeout(function() {
                // Get the search URL from data attribute or construct it
                const searchUrl = searchInput.dataset.searchUrl || '/panel/search/api/';
                
                fetch(searchUrl + "?q=" + encodeURIComponent(query))
                    .then(function(res) { return res.json(); })
                    .then(function(data) {
                        if (data.results && data.results.length > 0) {
                            let html = '';
                            data.results.forEach(function(user) {
                                const roleClass = user.role === 'student' ? 'role-student' : 'role-teacher';
                                const roleLabel = user.role === 'student' ? 'Student' : 'Teacher';
                                html += '<div class="search-result-item">' +
                                    '<div class="search-result-info">' +
                                        '<div class="search-result-name">' + AdminDashboard.escapeHtml(user.name) + '</div>' +
                                        '<div class="search-result-details">' +
                                            '<span class="search-result-role ' + roleClass + '">' + roleLabel + '</span>' +
                                            '<span><i class="fas fa-envelope"></i> ' + AdminDashboard.escapeHtml(user.email || 'N/A') + '</span>' +
                                            '<span><i class="fas fa-id-card"></i> ' + AdminDashboard.escapeHtml(user.username) + '</span>' +
                                        '</div>' +
                                    '</div>' +
                                    '<a href="' + user.edit_url + '" class="search-quick-view">Quick View</a>' +
                                '</div>';
                            });
                            searchResults.innerHTML = html;
                        } else {
                            searchResults.innerHTML = '<div class="search-no-results"><i class="fas fa-search"></i><p>No results found</p></div>';
                        }
                    })
                    .catch(function() {
                        searchResults.innerHTML = '<div class="search-no-results"><p>Search error. Please try again.</p></div>';
                    });
            }, 300);
        });

        // Close search results when clicking outside
        document.addEventListener('click', function(e) {
            if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
                searchResults.classList.remove('active');
            }
        });

        // Reopen search results on focus if there's content
        searchInput.addEventListener('focus', function() {
            if (searchResults.innerHTML.trim() !== '') {
                searchResults.classList.add('active');
            }
        });
    },

    escapeHtml: function(text) {
        var div = document.createElement('div');
        div.appendChild(document.createTextNode(text));
        return div.innerHTML;
    }
};

/**
 * Admin Statistics - Chart.js Integration
 * Renders statistical charts for data visualization
 */
const AdminStatistics = {
    themeColors: {
        primary: '#667eea',
        primaryLight: 'rgba(102, 126, 234, 0.15)',
        purple: '#764ba2',
        green: '#56ab2f',
        greenLight: 'rgba(86, 171, 47, 0.15)',
        orange: '#f2994a',
        blue: '#4facfe',
    },

    chartFont: {
        family: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
        size: 12
    },

    init: function(data) {
        if (!data) {
            return; // No data provided
        }

        if (data.monthlyData && data.yearlyData) {
            this.initMonthlyGrowthChart(data.monthlyData);
            this.initYearlyStatsChart(data.yearlyData);
            
            if (data.monthlyEnrollData) {
                this.initTrendChart(data.monthlyData, data.monthlyEnrollData);
            }
            
            if (data.gradeLabels && data.gradeCounts) {
                this.initGradeChart(data.gradeLabels, data.gradeCounts);
            }
        }
    },

    initMonthlyGrowthChart: function(monthlyData) {
        const canvas = document.getElementById('monthlyGrowthChart');
        if (!canvas) return;

        new Chart(canvas, {
            type: 'line',
            data: {
                labels: monthlyData.labels,
                datasets: [{
                    label: 'New Students',
                    data: monthlyData.counts,
                    borderColor: this.themeColors.primary,
                    backgroundColor: this.themeColors.primaryLight,
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 5,
                    pointBackgroundColor: this.themeColors.primary,
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointHoverRadius: 7,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { labels: { font: this.chartFont } }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { stepSize: 1, font: this.chartFont },
                        grid: { color: 'rgba(0,0,0,0.05)' }
                    },
                    x: {
                        ticks: { font: this.chartFont },
                        grid: { display: false }
                    }
                }
            }
        });
    },

    initYearlyStatsChart: function(yearlyData) {
        const canvas = document.getElementById('yearlyStatsChart');
        if (!canvas) return;

        new Chart(canvas, {
            type: 'bar',
            data: {
                labels: yearlyData.labels,
                datasets: [{
                    label: 'Students Joined',
                    data: yearlyData.counts,
                    backgroundColor: [
                        this.themeColors.primary, 
                        this.themeColors.purple, 
                        this.themeColors.green, 
                        this.themeColors.orange, 
                        this.themeColors.blue
                    ],
                    borderRadius: 8,
                    borderSkipped: false,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { labels: { font: this.chartFont } }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { stepSize: 1, font: this.chartFont },
                        grid: { color: 'rgba(0,0,0,0.05)' }
                    },
                    x: {
                        ticks: { font: this.chartFont },
                        grid: { display: false }
                    }
                }
            }
        });
    },

    initTrendChart: function(monthlyData, monthlyEnrollData) {
        const canvas = document.getElementById('trendChart');
        if (!canvas) return;

        new Chart(canvas, {
            type: 'line',
            data: {
                labels: monthlyData.labels,
                datasets: [
                    {
                        label: 'Students',
                        data: monthlyData.counts,
                        borderColor: this.themeColors.primary,
                        backgroundColor: this.themeColors.primaryLight,
                        borderWidth: 3,
                        fill: true,
                        tension: 0.4,
                        pointRadius: 4,
                        pointBackgroundColor: this.themeColors.primary,
                    },
                    {
                        label: 'Enrollments',
                        data: monthlyEnrollData.counts,
                        borderColor: this.themeColors.green,
                        backgroundColor: this.themeColors.greenLight,
                        borderWidth: 3,
                        fill: true,
                        tension: 0.4,
                        pointRadius: 4,
                        pointBackgroundColor: this.themeColors.green,
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { labels: { font: this.chartFont } }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { stepSize: 1, font: this.chartFont },
                        grid: { color: 'rgba(0,0,0,0.05)' }
                    },
                    x: {
                        ticks: { font: this.chartFont },
                        grid: { display: false }
                    }
                }
            }
        });
    },

    initGradeChart: function(gradeLabels, gradeCounts) {
        const canvas = document.getElementById('gradeChart');
        if (!canvas) return;

        new Chart(canvas, {
            type: 'doughnut',
            data: {
                labels: gradeLabels,
                datasets: [{
                    data: gradeCounts,
                    backgroundColor: [
                        this.themeColors.primary, 
                        this.themeColors.green, 
                        this.themeColors.orange, 
                        this.themeColors.blue, 
                        '#e74c3c'
                    ],
                    borderWidth: 2,
                    borderColor: '#fff',
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { font: this.chartFont, padding: 15 }
                    }
                }
            }
        });
    }
};

// Auto-initialize dashboard search when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    AdminDashboard.init();
});

// Export for use in templates
window.AdminDashboard = AdminDashboard;
window.AdminStatistics = AdminStatistics;
