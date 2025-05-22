// DOM 元素引用
const elements = {
    searchInput: document.getElementById('search-input'),
    searchButton: document.getElementById('search-button'),
    mobileMenuButton: document.getElementById('mobile-menu-button'),
    sidebar: document.querySelector('.sidebar'),
    sidebarOverlay: document.getElementById('sidebar-overlay'),
    sidebarNavList: document.getElementById('sidebar-nav-list'),
    categoriesContainer: document.getElementById('categories-container'),
    noResults: document.getElementById('no-results'),
    themeToggle: document.getElementById('theme-toggle'),
    themeIcon: document.getElementById('theme-icon'),
    htmlElement: document.documentElement,
    backToTopButton: document.getElementById('back-to-top')
};

// 网站分类数据
let websiteCategories = [];

// 工具函数
const utils = {
    // 防抖函数
    debounce(func, delay) {
        let timeoutId;
        return function (...args) {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => {
                func.apply(this, args);
            }, delay);
        };
    },

    // 加载状态管理
    showLoading() {
        elements.categoriesContainer.innerHTML = `
            <div class="loading-message text-center py-12">
                <i class="fa-solid fa-circle-notch fa-spin text-4xl text-primary mb-4"></i>
                <p class="text-xl text-gray-700 dark:text-gray-300">正在加载网站数据...</p>
            </div>
        `;
    },

    showError(message) {
        elements.categoriesContainer.innerHTML = `
            <div class="error-message text-center py-12">
                <i class="fa-solid fa-exclamation-triangle text-4xl text-red-500 mb-4"></i>
                <p class="text-xl text-gray-700 dark:text-gray-300">${message}</p>
            </div>
        `;
    },

    // 检测设备类型
    detectDeviceType() {
        const ua = navigator.userAgent;
        if (/(tablet|ipad|playbook|silk)|(android(?!.*mobi))/i.test(ua)) {
            return 'tablet';
        }
        if (/Mobile|Android|iP(hone|od)|IEMobile|BlackBerry|Kindle|Silk-Accelerated|(hpw|web)OS|Opera M(obi|ini)/.test(ua)) {
            return 'mobile';
        }
        return 'desktop';
    }
};

// 侧边栏管理
const sidebarManager = {
    init() {
        this.bindEvents();
    },

    bindEvents() {
        // 移动端菜单切换
        elements.mobileMenuButton.addEventListener('click', () => {
            elements.sidebar.classList.toggle('-translate-x-full');
            elements.sidebarOverlay.classList.toggle('hidden');
            document.body.classList.toggle('overflow-hidden');

            // 添加/移除遮罩层动画
            if (!elements.sidebarOverlay.classList.contains('hidden')) {
                setTimeout(() => {
                    elements.sidebarOverlay.classList.add('active');
                }, 10);
            } else {
                elements.sidebarOverlay.classList.remove('active');
            }
        });

        // 点击遮罩层关闭侧边栏
        elements.sidebarOverlay.addEventListener('click', () => {
            elements.sidebar.classList.add('-translate-x-full');
            elements.sidebarOverlay.classList.add('hidden', 'active');
            document.body.classList.remove('overflow-hidden');
        });

        // 窗口大小变化时处理
        window.addEventListener('resize', () => {
            if (window.innerWidth >= 768) {
                // 在桌面模式下确保侧边栏显示
                elements.sidebar.classList.remove('-translate-x-full');
                elements.sidebarOverlay.classList.add('hidden', 'active');
                document.body.classList.remove('overflow-hidden');
            } else if (!elements.sidebarOverlay.classList.contains('hidden')) {
                // 在移动模式下如果侧边栏是打开的，则保持打开状态
                document.body.classList.add('overflow-hidden');
                setTimeout(() => {
                    elements.sidebarOverlay.classList.add('active');
                }, 10);
            }
        });
    },

    updateActiveLink(elementId) {
        // 移除所有激活状态
        document.querySelectorAll('.sidebar-link.active').forEach(link => {
            link.classList.remove('active', 'bg-primary/10', 'text-primary');
            link.classList.add('text-gray-700', 'dark:text-gray-300');
        });

        // 添加新的激活状态
        const activeLink = document.querySelector(`.sidebar-link[data-id="${elementId}"]`);
        if (activeLink) {
            activeLink.classList.add('active', 'bg-primary/10', 'text-primary');
            activeLink.classList.remove('text-gray-700', 'dark:text-gray-300');
        }

        // 获取当前激活的分类ID
        const currentCategoryId = elementId.split('-')[0];

        // 防止滚动到不存在的分类
        if (!document.querySelector(`.submenu[data-category="${currentCategoryId}"]`)) return;

        // 关闭所有其他分类的子菜单
        document.querySelectorAll('.submenu[data-category]').forEach(submenu => {
            if (submenu.dataset.category !== currentCategoryId && submenu.classList.contains('expanded')) {
                this.toggleSubmenu(submenu.previousElementSibling);
            }
        });

        // 确保当前父级菜单展开
        const parentMenu = document.querySelector(`.submenu[data-category="${currentCategoryId}"]`);
        if (parentMenu && !parentMenu.classList.contains('expanded')) {
            this.toggleSubmenu(parentMenu.previousElementSibling);
        }
    },

    toggleSubmenu(menuItem) {
        const submenu = menuItem.nextElementSibling;
        const icon = menuItem.querySelector('.expand-icon');

        // 切换展开/折叠状态
        submenu.classList.toggle('expanded');
        icon.classList.toggle('fa-chevron-down');
        icon.classList.toggle('fa-chevron-right');

        // 添加动画效果
        if (submenu.classList.contains('expanded')) {
            submenu.style.maxHeight = submenu.scrollHeight + 'px';
        } else {
            submenu.style.maxHeight = '0px';
        }
    }
};

// 网站内容渲染
const contentRenderer = {
    // 创建网站卡片
    createWebsiteCard(website) {
        const card = document.createElement('div');
        card.className = 'website-card bg-white dark:bg-neutral-700';
        card.dataset.websiteId = website.name;

        card.innerHTML = `
            <a href="${website.url}" target="_blank" class="website-link block">
                <div class="website-header flex items-center gap-3 mb-3">
                    <div class="website-icon bg-neutral-100 dark:bg-neutral-700">
                        <img 
                        src="${website.icon}" 
                        alt="${website.name}" 
                        class="max-w-full max-h-full object-contain transition-transform"  /* 所有样式通过类名定义 */
                        onerror="this.src='/fallback-icon.png'" 
                        />
            </div>
                <h3 class="website-title font-medium text-neutral-800 dark:text-neutral-200">${website.name}</h3>
                </div>
                    <p class="website-description text-sm text-neutral-600 dark:text-neutral-400">${website.description}</p>
            </a>
`;
        return card;
    },

    // 初始化侧边栏导航
    initSidebarNav() {
        elements.sidebarNavList.innerHTML = '';

        websiteCategories.forEach((category, index) => {
            const hasSubsections = category.sections.some(section => section.name);

            // 创建一级菜单
            const categoryLi = document.createElement('li');
            categoryLi.className = 'mb-1';

            // 如果有子部分，创建可展开的菜单
            if (hasSubsections) {
                const categoryLink = document.createElement('a');
                categoryLink.href = `#${category.id}`;
                categoryLink.className = `sidebar-link flex items-center justify-between py-2 px-4 rounded-lg text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700 transition-colors`;
                categoryLink.dataset.category = category.id;

                categoryLink.innerHTML = `
                <div class="flex items-center">
                    <i class="fa-solid fa-${category.icon} mr-3 w-5 text-center"></i>
                    <span>${category.name}</span>
                </div>
                <i class="fa-chevron-right expand-icon text-xs transition-transform"></i>
            `;

                categoryLi.appendChild(categoryLink);

                // 创建子菜单（默认展开第一个分类）
                const submenu = document.createElement('ul');
                submenu.className = `submenu pl-8 mt-1 overflow-hidden transition-all duration-300 ease-in-out ${index === 0 ? 'expanded' : ''}`;
                submenu.dataset.category = category.id;

                // 设置初始高度
                if (index === 0) {
                    // 使用 requestAnimationFrame 确保内容渲染后再设置高度
                    requestAnimationFrame(() => {
                        // 先临时显示子菜单以获取其实际高度
                        submenu.style.display = 'block';
                        const height = submenu.scrollHeight;
                        submenu.style.display = ''; // 恢复隐藏状态
                        submenu.style.maxHeight = height + 'px';
                        categoryLink.querySelector('.expand-icon').classList.remove('fa-chevron-right');
                        categoryLink.querySelector('.expand-icon').classList.add('fa-chevron-down');
                    });
                } else {
                    submenu.style.maxHeight = '0px';
                }

                // 为每个有名称的子部分创建菜单项
                const namedSections = category.sections.filter(section => section.name);

                // 添加所有子项
                namedSections.forEach((section, sectionIndex) => {
                    const sectionId = `${category.id}-${category.sections.indexOf(section)}`;

                    const sectionLi = document.createElement('li');
                    sectionLi.className = 'mb-1';

                    const sectionLink = document.createElement('a');
                    sectionLink.href = `#${sectionId}`;
                    sectionLink.className = 'sidebar-link flex items-center py-2 px-4 rounded-lg text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700 transition-colors';
                    sectionLink.dataset.id = sectionId;
                    sectionLink.innerHTML = `
                    <i class="fa-circle text-xs mr-3 text-gray-400"></i>
                    <span>${section.name}</span>
                `;

                    sectionLi.appendChild(sectionLink);
                    submenu.appendChild(sectionLi);
                });

                categoryLi.appendChild(submenu);

                // 添加点击事件
                categoryLink.addEventListener('click', (e) => {
                    e.preventDefault();
                    const submenu = categoryLink.nextElementSibling;
                    const icon = categoryLink.querySelector('.expand-icon');

                    // 切换展开/折叠状态
                    submenu.classList.toggle('expanded');
                    icon.classList.toggle('fa-chevron-down');
                    icon.classList.toggle('fa-chevron-right');

                    // 添加动画效果
                    if (submenu.classList.contains('expanded')) {
                        submenu.style.maxHeight = submenu.scrollHeight + 'px';
                    } else {
                        submenu.style.maxHeight = '0px';
                    }
                });

            } else {
                // 如果没有子部分，创建普通菜单项
                const categoryLink = document.createElement('a');
                categoryLink.href = `#${category.id}`;
                categoryLink.className = `sidebar-link flex items-center py-2 px-4 rounded-lg text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700 transition-colors`;
                categoryLink.dataset.id = category.id;

                categoryLink.innerHTML = `
                <i class="fa-solid fa-${category.icon} mr-3 w-5 text-center"></i>
                <span>${category.name}</span>
            `;

                categoryLi.appendChild(categoryLink);
            }

            elements.sidebarNavList.appendChild(categoryLi);
        });

        // 重新绑定侧边栏链接事件
        document.querySelectorAll('.sidebar-link[data-id]').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();

                // 更新活跃状态
                sidebarManager.updateActiveLink(link.dataset.id);

                // 关闭移动端侧边栏
                if (window.innerWidth < 768) {
                    elements.sidebar.classList.add('-translate-x-full');
                    elements.sidebarOverlay.classList.add('hidden', 'active');
                    document.body.classList.remove('overflow-hidden');
                }

                // 平滑滚动到对应区域
                const targetId = link.dataset.id;
                const targetElement = document.getElementById(targetId);
                if (targetElement) {
                    const headerOffset = 80;
                    const elementPosition = targetElement.getBoundingClientRect().top;
                    const offsetPosition = elementPosition + window.pageYOffset - headerOffset;

                    window.scrollTo({
                        top: offsetPosition,
                        behavior: 'smooth'
                    });
                }
            });
        });
    },
    // 初始化网站列表
    initWebsitesList() {
        elements.categoriesContainer.innerHTML = '';

        // 为每个分类创建容器和网站卡片
        websiteCategories.forEach(category => {
            const section = document.createElement('section');
            section.id = category.id;
            section.className = 'category-section mb-12';

            // 创建分类标题
            const categoryHeader = document.createElement('div');
            categoryHeader.className = 'category-header mb-6';
            categoryHeader.innerHTML = `
                <h2 class="category-title text-2xl font-bold mb-2 flex items-center">
                    <i class="fa-solid fa-${category.icon} text-primary mr-3"></i>
                    ${category.name}
                </h2>
                ${category.description ? `<p class="category-description text-neutral-600 dark:text-neutral-400">${category.description}</p>` : ''}
            `;

            section.appendChild(categoryHeader);

            // 为每个子部分创建容器
            category.sections.forEach((sectionData, sectionIndex) => {
                const sectionId = `${category.id}-${sectionIndex}`;
                const subSection = document.createElement('div');
                subSection.id = sectionId;
                subSection.className = `sub-section mb-8 ${sectionIndex > 0 ? 'border-t border-neutral-200 dark:border-neutral-700 pt-8' : ''}`;

                // 创建子部分标题（二级标题）
                if (sectionData.name) {
                    const subSectionTitle = document.createElement('h3');
                    subSectionTitle.className = 'sub-section-title text-xl font-semibold mb-4';
                    subSectionTitle.textContent = sectionData.name;
                    subSection.appendChild(subSectionTitle);
                }

                // 创建网站网格
                const websitesGrid = document.createElement('div');
                websitesGrid.className = 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 websites-grid';
                websitesGrid.id = `${sectionId}-websites`;

                // 添加网站卡片
                if (sectionData.websites && sectionData.websites.length > 0) {
                    sectionData.websites.forEach(website => {
                        const card = this.createWebsiteCard(website);
                        websitesGrid.appendChild(card);
                    });
                }

                subSection.appendChild(websitesGrid);
                section.appendChild(subSection);
            });

            elements.categoriesContainer.appendChild(section);
        });

        elements.noResults.classList.add('hidden');
    }
};

// 搜索功能
const searchManager = {
    init() {
        this.bindEvents();
    },

    bindEvents() {
        // 搜索按钮点击事件
        elements.searchButton.addEventListener('click', this.searchWebsites.bind(this));

        // 搜索输入框回车事件
        elements.searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                this.searchWebsites();
            }
        });

        // 添加输入事件监听
        elements.searchInput.addEventListener('input', utils.debounce(this.searchWebsites.bind(this), 300));
    },

    searchWebsites() {
        const searchTerm = elements.searchInput.value.toLowerCase().trim();
        let hasResults = false;

        // 如果搜索词为空，重新初始化所有网站
        if (!searchTerm) {
            contentRenderer.initWebsitesList();
            return;
        }

        // 隐藏所有分类
        document.querySelectorAll('.category-section').forEach(section => {
            section.classList.add('hidden');
        });

        // 隐藏全局提示
        elements.noResults.classList.add('hidden');

        // 清空所有分类容器
        document.querySelectorAll('.websites-grid').forEach(container => {
            container.innerHTML = '';
        });

        // 搜索并显示匹配的网站
        websiteCategories.forEach(category => {
            let categoryHasResults = false;

            category.sections.forEach((sectionData, sectionIndex) => {
                const matchedWebsites = sectionData.websites
                    ? sectionData.websites.filter(website =>
                        website.name.toLowerCase().includes(searchTerm) ||
                        website.description.toLowerCase().includes(searchTerm)
                    )
                    : [];

                if (matchedWebsites.length > 0) {
                    const sectionId = `${category.id}-${sectionIndex}`;
                    const websitesGrid = document.getElementById(`${category.id}-${sectionIndex}-websites`);
                    matchedWebsites.forEach(website => {
                        const card = contentRenderer.createWebsiteCard(website);
                        websitesGrid.appendChild(card);
                    });

                    // 确保子部分和分类显示
                    const subSection = document.getElementById(sectionId);
                    if (subSection) {
                        subSection.classList.remove('hidden');
                    }

                    document.getElementById(category.id).classList.remove('hidden');
                    categoryHasResults = true;
                    hasResults = true;
                } else {
                    // 隐藏没有结果的子部分
                    const sectionId = `${category.id}-${sectionIndex}`;
                    const subSection = document.getElementById(sectionId);
                    if (subSection) {
                        subSection.classList.add('hidden');
                    }
                }
            });
        });

        // 处理无结果情况
        if (!hasResults) {
            document.getElementById('search-query').textContent = searchTerm;
            elements.noResults.classList.remove('hidden');
            window.scrollTo({ top: 0, behavior: 'smooth' });
        } else {
            // 滚动到第一个结果
            const firstResult = document.querySelector('.website-card');
            if (firstResult) {
                firstResult.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }
    }
};

// 滚动管理
const scrollManager = {
    init() {
        // 使用防抖减少滚动事件触发频率
        window.addEventListener('scroll', utils.debounce(this.handleScroll.bind(this), 50));

        // 初始化回到顶部按钮
        elements.backToTopButton.addEventListener('click', () => {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    },

    handleScroll() {
        const scrollPosition = window.scrollY;
        const sections = document.querySelectorAll('.sub-section:not(.hidden)');

        let currentSection = websiteCategories[0]?.id || ''; // 默认选中第一个分类

        // 计算当前可见区域的中心点
        const viewportHeight = window.innerHeight;
        const viewportCenter = scrollPosition + viewportHeight / 2;

        // 找到包含视口中心点的区域
        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            const sectionBottom = sectionTop + section.offsetHeight;

            if (viewportCenter >= sectionTop && viewportCenter <= sectionBottom) {
                currentSection = section.id;
            }
        });

        // 更新侧边栏活跃状态
        sidebarManager.updateActiveLink(currentSection);

        // 控制回到顶部按钮显示/隐藏
        if (scrollPosition > 300) {
            elements.backToTopButton.classList.remove('opacity-0', 'invisible');
            elements.backToTopButton.classList.add('opacity-100', 'visible');
        } else {
            elements.backToTopButton.classList.add('opacity-0', 'invisible');
            elements.backToTopButton.classList.remove('opacity-100', 'visible');
        }

        // 控制导航栏样式
        const header = document.querySelector('.header');
        if (scrollPosition > 50) {
            header.classList.add('shadow-md');
            header.classList.remove('shadow-sm');
        } else {
            header.classList.remove('shadow-md');
            header.classList.add('shadow-sm');
        }
    }
};

// 主题切换管理
const themeManager = {
    init() {
        this.bindEvents();
        this.updateThemeIcon();

        // 初始化主题
        if (localStorage.theme === 'dark' || (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
            elements.htmlElement.classList.add('dark');
        } else {
            elements.htmlElement.classList.remove('dark');
        }
    },

    bindEvents() {
        elements.themeToggle.addEventListener('click', () => {
            // 切换主题
            if (elements.htmlElement.classList.contains('dark')) {
                elements.htmlElement.classList.remove('dark');
                localStorage.theme = 'light';
            } else {
                elements.htmlElement.classList.add('dark');
                localStorage.theme = 'dark';
            }

            // 更新按钮图标和颜色
            this.updateThemeIcon();
        });

        // 监听系统主题变化
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
            if (localStorage.theme === 'system' || !('theme' in localStorage)) {
                elements.htmlElement.classList.toggle('dark', e.matches);
                this.updateThemeIcon();
            }
        });
    },

    updateThemeIcon() {
        const isDark = elements.htmlElement.classList.contains('dark');

        // 更新图标
        elements.themeIcon.className = isDark
            ? 'fa-solid fa-sun text-xl'
            : 'fa-solid fa-moon text-xl';

        // 更新按钮背景和文字颜色
        elements.themeToggle.className = isDark
            ? 'fixed bottom-20 right-6 bg-neutral-900 text-secondary rounded-full p-3 shadow-lg transition-all duration-300 hover:scale-110'
            : 'fixed bottom-20 right-6 bg-white text-primary rounded-full p-3 shadow-lg transition-all duration-300 hover:scale-110';
    }
};

// 响应式布局管理
const responsiveManager = {
    init() {
        this.applyLayoutBasedOnDevice();
        window.addEventListener('resize', this.applyLayoutBasedOnDevice.bind(this));
    },

    applyLayoutBasedOnDevice() {
        const device = utils.detectDeviceType();
        const websitesGrids = document.querySelectorAll('.websites-grid');

        // 根据设备类型调整布局
        websitesGrids.forEach(grid => {
            grid.className = 'grid gap-6 websites-grid';

            if (device === 'desktop') {
                grid.classList.add('grid-cols-3');
            } else if (device === 'tablet') {
                grid.classList.add('grid-cols-2');
            } else {
                grid.classList.add('grid-cols-1');
            }
        });
    }
};

// 数据加载
async function loadWebsiteData() {
    utils.showLoading();

    try {
        const response = await fetch('assets/data/websites.yaml');
        const yamlText = await response.text();
        websiteCategories = jsyaml.load(yamlText);

        // 初始化各模块
        contentRenderer.initSidebarNav();
        contentRenderer.initWebsitesList();
        sidebarManager.init();
        searchManager.init();
        scrollManager.init();
        themeManager.init();
        responsiveManager.init();

        // 默认选中第一个分类
        const firstCategoryId = websiteCategories[0]?.id;
        if (firstCategoryId) {
            sidebarManager.updateActiveLink(firstCategoryId);
        }

        // 平滑滚动到顶部
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    } catch (error) {
        console.error('加载网站数据失败:', error);
        utils.showError('无法加载网站数据，请稍后再试。');
    }
}

// 初始化页面
document.addEventListener('DOMContentLoaded', loadWebsiteData);    