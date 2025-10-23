// 添加页面加载动画
window.addEventListener('DOMContentLoaded', () => {
    // 为所有区块添加渐入效果
    const sections = document.querySelectorAll('section, .header');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = 1;
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, { threshold: 0.1 });
    
    sections.forEach(section => {
        section.style.opacity = 0;
        section.style.transform = 'translateY(30px)';
        section.style.transition = 'opacity 0.8s ease, transform 0.8s ease';
        observer.observe(section);
    });

    // 为抖音链接添加点击效果
    const douyinLink = document.querySelector('.douyin-link');
    if (douyinLink) {
        douyinLink.addEventListener('click', function(e) {
            this.style.transform = 'scale(0.95)';
            setTimeout(() => {
                this.style.transform = 'scale(1)';
            }, 150);
        });
    }

    // 平滑滚动效果
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                window.scrollTo({
                    top: targetElement.offsetTop - 20,
                    behavior: 'smooth'
                });
            }
        });
    });

    // 添加鼠标跟随效果
    const cursor = document.createElement('div');
    cursor.classList.add('cursor-fx');
    document.body.appendChild(cursor);

    document.addEventListener('mousemove', (e) => {
        cursor.style.left = e.clientX + 'px';
        cursor.style.top = e.clientY + 'px';
    });

    // 为链接和可点击元素添加交互效果
    const interactiveElements = document.querySelectorAll('a, button, .highlight-card.clickable');
    interactiveElements.forEach(element => {
        element.addEventListener('mouseenter', () => {
            cursor.style.transform = 'scale(1.5)';
            cursor.style.backgroundColor = 'rgba(255, 44, 85, 0.3)';
        });
        
        element.addEventListener('mouseleave', () => {
            cursor.style.transform = 'scale(1)';
            cursor.style.backgroundColor = 'rgba(102, 126, 234, 0.5)';
        });
    });
    
    // 时间轴拖动功能增强
    const timelineWrapper = document.querySelector('.timeline-scroll-wrapper');
    let isDragging = false;
    let startX;
    let scrollLeft;

    if (timelineWrapper) {
        // 鼠标拖动事件
        timelineWrapper.addEventListener('mousedown', (e) => {
            isDragging = true;
            startX = e.pageX - timelineWrapper.offsetLeft;
            scrollLeft = timelineWrapper.scrollLeft;
            timelineWrapper.style.cursor = 'grabbing';
        });

        timelineWrapper.addEventListener('mouseleave', () => {
            isDragging = false;
            timelineWrapper.style.cursor = 'grab';
        });

        timelineWrapper.addEventListener('mouseup', () => {
            isDragging = false;
            timelineWrapper.style.cursor = 'grab';
        });

        timelineWrapper.addEventListener('mousemove', (e) => {
            if (!isDragging) return;
            e.preventDefault();
            const x = e.pageX - timelineWrapper.offsetLeft;
            const walk = (x - startX) * 1.5; // 拖动速度
            timelineWrapper.scrollLeft = scrollLeft - walk;
        });

        // 触摸事件支持
        timelineWrapper.addEventListener('touchstart', (e) => {
            if (e.touches.length === 1) {
                isDragging = true;
                startX = e.touches[0].pageX - timelineWrapper.offsetLeft;
                scrollLeft = timelineWrapper.scrollLeft;
            }
        }, { passive: true });

        timelineWrapper.addEventListener('touchend', () => {
            isDragging = false;
        });

        timelineWrapper.addEventListener('touchmove', (e) => {
            if (!isDragging || e.touches.length !== 1) return;
            const x = e.touches[0].pageX - timelineWrapper.offsetLeft;
            const walk = (x - startX) * 1.5;
            timelineWrapper.scrollLeft = scrollLeft - walk;
        }, { passive: true });

        // 设置初始光标样式
        timelineWrapper.style.cursor = 'grab';
        
        // 添加惯性滚动提示（可选）
        let isScrolling = false;
        timelineWrapper.addEventListener('scroll', () => {
            if (!isScrolling) {
                window.requestAnimationFrame(() => {
                    // 这里可以添加滚动时的动画效果
                    isScrolling = false;
                });
            }
            isScrolling = true;
        });
    }

    // 为内容亮点卡片添加点击事件
    const highlightCards = document.querySelectorAll('.highlight-card.clickable');
    highlightCards.forEach(card => {
        card.addEventListener('click', () => {
            const content = card.getAttribute('data-content');
            // 创建一个临时弹窗来显示信息
            const popup = document.createElement('div');
            popup.className = 'info-popup';
            popup.innerHTML = `
                <div class="popup-content">
                    <h3>${content}</h3>
                    <p>正在加载相关内容...</p>
                    <button class="close-popup">关闭</button>
                </div>
            `;
            document.body.appendChild(popup);
            
            // 为关闭按钮添加事件
            const closeBtn = popup.querySelector('.close-popup');
            closeBtn.addEventListener('click', () => {
                document.body.removeChild(popup);
            });
            
            // 点击弹窗外部关闭
            popup.addEventListener('click', (e) => {
                if (e.target === popup) {
                    document.body.removeChild(popup);
                }
            });
            
            // 添加键盘ESC关闭功能
            const closePopup = (e) => {
                if (e.key === 'Escape') {
                    if (document.body.contains(popup)) {
                        document.body.removeChild(popup);
                    }
                    document.removeEventListener('keydown', closePopup);
                }
            };
            document.addEventListener('keydown', closePopup);
        });
    });

    // 添加一些统计数据的动画效果
    animateStats();
});

// 统计数据动画函数
function animateStats() {
    const statNumbers = document.querySelectorAll('.stat-number');
    
    statNumbers.forEach(number => {
        // 保存原始文本，用于恢复
        const originalText = number.innerText;
        
        // 直接使用原始值，不做动画处理，避免数字格式错误
        number.innerText = originalText;
    });
}

// 添加窗口大小变化时的响应
window.addEventListener('resize', () => {
    // 重置动画状态
    const sections = document.querySelectorAll('section, .header');
    sections.forEach(section => {
        section.style.opacity = '';
        section.style.transform = '';
    });
    
    // 重新触发动画
    setTimeout(() => {
        sections.forEach(section => {
            section.style.opacity = 0;
            section.style.transform = 'translateY(30px)';
            setTimeout(() => {
                section.style.opacity = 1;
                section.style.transform = 'translateY(0)';
            }, 100);
        });
    }, 100);
});

// 添加错误处理
window.addEventListener('error', (event) => {
    console.error('发生错误:', event.error);
});

// 添加页面可见性变化监听
document.addEventListener('visibilitychange', () => {
    if (!document.hidden) {
        // 页面重新可见时，可以添加一些恢复动画或数据刷新逻辑
        console.log('页面重新可见');
    }
});