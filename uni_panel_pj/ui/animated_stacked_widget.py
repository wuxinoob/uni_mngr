from PySide6.QtWidgets import QStackedWidget, QWidget
from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QPoint, QParallelAnimationGroup

class AnimatedStackedWidget(QStackedWidget):
    def __init__(self, parent=None):
        super(AnimatedStackedWidget, self).__init__(parent)
        self.m_speed = 500  # Animation speed in milliseconds
        self.m_animation_type = QEasingCurve.Type.OutCubic
        self.m_now = 0
        self.m_next = 0
        self.m_wrap = False
        self.m_pnow = QPoint(0, 0)
        self.m_active = False

    def setSpeed(self, speed):
        self.m_speed = speed

    def setAnimation(self, animation_type):
        self.m_animation_type = animation_type

    def setWrap(self, wrap):
        self.m_wrap = wrap

    def slideInNext(self):
        now_index = self.currentIndex()
        if self.m_wrap:
            next_index = (now_index + 1) % self.count()
        else:
            next_index = min(now_index + 1, self.count() - 1)
        self.slideInIdx(next_index)

    def slideInPrev(self):
        now_index = self.currentIndex()
        if self.m_wrap:
            next_index = (now_index - 1 + self.count()) % self.count()
        else:
            next_index = max(now_index - 1, 0)
        self.slideInIdx(next_index)

    def slideInIdx(self, index):
        if self.currentIndex() == index:
            return
            
        if self.m_active:
            return
        self.m_active = True

        self.m_now = self.currentIndex()
        self.m_next = index

        widget_now = self.widget(self.m_now)
        widget_next = self.widget(self.m_next)

        if not widget_now or not widget_next:
            self.m_active = False
            return
            
        w = self.width()
        h = self.height()
        
        # Determine direction
        if self.m_now < self.m_next:
            # Slide Left
            pnext = QPoint(w, 0)
            pnow = QPoint(-w, 0)
        else:
            # Slide Right
            pnext = QPoint(-w, 0)
            pnow = QPoint(w, 0)

        widget_next.setGeometry(pnext.x(), 0, w, h)
        widget_next.show()
        widget_next.raise_()

        anim_now = QPropertyAnimation(widget_now, b"pos")
        anim_now.setDuration(self.m_speed)
        anim_now.setEasingCurve(self.m_animation_type)
        anim_now.setEndValue(pnow)

        anim_next = QPropertyAnimation(widget_next, b"pos")
        anim_next.setDuration(self.m_speed)
        anim_next.setEasingCurve(self.m_animation_type)
        anim_next.setEndValue(QPoint(0,0))
        
        self.m_anim_group = QParallelAnimationGroup()
        self.m_anim_group.addAnimation(anim_now)
        self.m_anim_group.addAnimation(anim_next)
        
        self.m_anim_group.finished.connect(self.animationDone)
        
        super().setCurrentIndex(self.m_next)
        
        self.m_anim_group.start()
        
    def animationDone(self):
        self.widget(self.m_now).hide()
        self.widget(self.m_now).move(self.m_pnow)
        self.m_active = False

    def setCurrentIndex(self, index):
        self.slideInIdx(index)
