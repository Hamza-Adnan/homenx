#include "XmbLayout.hpp"
#include <cassert>

int main() {
    using namespace cards::xmb;
    // Empty and end-of-library input must never produce an invalid index.
    assert(step(0, -1, 0) == 0);
    assert(step(0, 1, 0) == 0);
    assert(step(0, -1, 1) == 0);
    assert(step(0, 1, 1) == 0);
    assert(step(0, -1, 1000) == 0);
    assert(step(999, 1, 1000) == 999);
    assert(step(4, -1, 10) == 3);
    assert(step(4, 1, 10) == 5);
    // Selection stays anchored as the list scrolls, including large libraries.
    for (int selected : {0, 1, 50, 999}) {
        auto item = itemRect(selected, static_cast<float>(selected));
        assert(item.center().x == axisX);
        assert(item.center().y == itemY);
        assert(item.width == 76.f);
        auto hit = itemHit(selected, static_cast<float>(selected));
        assert(hit.contains(500.f, itemY));
        assert(!hit.contains(500.f, itemY + itemPitch));
    }
    auto halfway = itemRect(5, 4.5f);
    assert(halfway.center().y == itemY + itemPitch * .5f);
    assert(halfway.width == 60.f);
    assert(categoryX(2, 2) == axisX);
    assert(categoryX(1, 2) == axisX - categoryPitch);
    assert(categoryX(3, 2) == axisX + categoryPitch);

    assert(focus(0.f) == 1.f);
    assert(focus(1.f) == 0.f && focus(-1.f) == 0.f);
    assert(focus(.5f) == .5f);
    // A single press accelerates and settles without crossing its destination.
    float position = 0.f, velocity = 0.f, previous = 0.f;
    for (int frame = 0; frame < 90; ++frame) {
        glide(position, velocity, 1.f, 1.f / 60.f);
        assert(position >= previous && position <= 1.f);
        previous = position;
    }
    assert(position == 1.f && velocity == 0.f);
    // The exact spring follows the same path at 30, 60 and 120 Hz.
    float results[3];
    int index = 0;
    for (int hz : {30, 60, 120}) {
        position = velocity = 0.f;
        for (int frame = 0; frame < hz / 5; ++frame)
            glide(position, velocity, 1.f, 1.f / hz);
        results[index++] = position;
    }
    assert(std::abs(results[0] - results[1]) < .00001f);
    assert(std::abs(results[1] - results[2]) < .00001f);
    assert(results[0] > .95f);
    // Retargeting retains momentum; reversal then settles in either direction.
    position = velocity = 0.f;
    glide(position, velocity, 1.f, .05f);
    const float movingVelocity = velocity;
    const float movingPosition = position;
    glide(position, velocity, -1.f, 0.f);
    assert(position == movingPosition && velocity == movingVelocity);
    for (int frame = 0; frame < 180; ++frame)
        glide(position, velocity, -1.f, 1.f / 120.f);
    assert(position == -1.f && velocity == 0.f);
    // Held navigation can retarget a spring many times without instability.
    position = velocity = 0.f;
    for (int frame = 0; frame < 600; ++frame) {
        glide(position, velocity, static_cast<float>(frame / 6), 1.f / 60.f);
        assert(std::isfinite(position) && std::isfinite(velocity));
    }
    for (int frame = 0; frame < 120; ++frame)
        glide(position, velocity, 99.f, 1.f / 60.f);
    assert(std::abs(position - 99.f) < .0001f);
}
