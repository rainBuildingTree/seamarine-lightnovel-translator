from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import QTimer, QRectF
from PyQt5.QtGui import QPainter, QColor, QPen

class RotatingButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(100, 100)
        self._animating = False
        self.setCheckable(True)
        self.angle = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_angle)

    def toggle_animation(self):
        if self.isChecked():
            self.timer.start(30)
        else:
            self.timer.stop()
            self.angle = 0
            self.update()

    def update_angle(self):
        self.angle = (self.angle + 6) % 360
        self.update()

    def start_animation(self):
        if not self._animating:
            self._animating = True
            self.timer.start(30)
        self.update()

    def stop_animation(self):
        if self._animating:
            self._animating = False
            self.timer.stop()
            self.angle = 0
            self.update()


    def paintEvent(self, event):
        super().paintEvent(event)

        if not self._animating:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        pen = QPen(QColor(158, 164, 200))
        pen.setWidth(3)
        painter.setPen(pen)

        painter.translate(self.width() / 2, self.height() / 2)
        painter.rotate(self.angle)
        painter.translate(-self.width() / 2, -self.height() / 2)

        margin = 2
        rect = QRectF(margin, margin, self.width() - 2 * margin, self.height() - 2 * margin)
        painter.drawArc(rect, 0 * 16, 120 * 16)