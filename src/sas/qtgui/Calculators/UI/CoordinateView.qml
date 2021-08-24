import QtQuick 2.15
import QtQuick3D 1.15
import QtQuick3D.Helpers 1.15

// This is the main qml file containing the full scene to be displayed in the generic scattering calculator
// It shows the three different coordinate systems and any vector properties

View3D {
    id: view
    anchors.fill: parent

    // background
    environment: SceneEnvironment {
        clearColor: "#000033"
        backgroundMode: SceneEnvironment.Color
    }

    // holds the 3D scene
    Node {
        id: scene

        PerspectiveCamera {
            id: camera
            objectName: "camera"
            fieldOfView: 30
            // theta angle from y axis to x-z plane
            // phi angle from x -> z CLOCKWISE direction
            property var theta: Math.PI/2
            property var phi: 0
            property var radius: 1130
            x: radius * Math.sin(theta) * Math.cos(phi)
            y: radius * Math.cos(theta)
            z: radius * Math.sin(theta) * Math.sin(phi)
            Component.onCompleted: lookAt(Qt.vector3d(0,0,0))

            // move the camera and repoint to the origin
            function updatePosition() {
                x = radius * Math.sin(theta) * Math.cos(phi)
                y = radius * Math.cos(theta)
                z = radius * Math.sin(theta) * Math.sin(phi)
                lookAt(Qt.vector3d(0,0,0))
            }

            // reset the camera location
            function reset() {
                theta = Math.PI/2
                phi = 0
                radius = 1130
                updatePosition()
            }
        }

        DirectionalLight {
            z: 300
            x: 300
            y: 300
            brightness: 100
            eulerRotation: Qt.vector3d(45, 45, -45)
        }

        // beamline coordinates
        Axes {objectName: "UVW"; axis_1: "U"; axis_2: "V"; axis_3: "W"; position: Qt.vector3d(0, 0, -400)}
        Node {
            Text {
                text: "BEAMLINE"
                font.pixelSize: 40
                color: "white"
            }
            position: Qt.vector3d(0, 200, -400)
            eulerRotation.y: 90
        }
        Model {
            source: "#Cube"
            scale: Qt.vector3d(1, 1, 0.01)
            position: Qt.vector3d(0, 0, -400)
            materials: DefaultMaterial {
                diffuseColor: "#888888"
                emissiveFactor: 0.5
            }
        }
        // environment coordinates
        // separate node so that the polarisation vector rotates with the frame
        Node {
            objectName: "uvw"
            rotation: Qt.quaternion(1, 0, 0, 0)
            Axes {axis_1: "u"; axis_2: "v"; axis_3: "w"; position: Qt.vector3d(0, 0, 0)}
            UnitVector {objectName: "polarisation"; vector_color: "#ff00bb"; vector_text: "p"}
        }
        Node {
            Text {
                text: "ENVIRONMENT"
                font.pixelSize: 40
                color: "white"
            }
            position: Qt.vector3d(0, 200, 0)
            eulerRotation.y: 90
        }
        // sample coordinates
        Axes {objectName: "xyz"; axis_1: "x"; axis_2: "y"; axis_3: "z"; position: Qt.vector3d(0, 0, 400)}
        Node {
            Text {
                text: "SAMPLE"
                font.pixelSize: 40
                color: "white"
            }
            position: Qt.vector3d(0, 200, 400)
            eulerRotation.y: 90
        }
        
    }

    // This object handles all of the interactions with the mouse
    // Implements a basic orbital camera which the user can control by clicking and dragging
    // dragging horizontally rotates in the x-z aximuthal plane
    // dragging vertically rotates in the polar angle from the y axis to the x-z plane
    // mouse wheel zooms the camera in and out
    MouseArea {
        id: mouseHandler
        property var dragging: false
        property var prev_x: 0
        property var prev_y: 0
        property var new_x: 0
        property var new_y: 0
        property var mouse_speed: 0.005
        property var scroll_speed: 0.1
        anchors.fill: parent
        hoverEnabled: true
        acceptedButtons: Qt.LeftButton
        onPressed: {
            dragging = true
            prev_x = mouse.x
            prev_y = mouse.y
        }
        onReleased: {
            dragging = false
        }
        onPositionChanged: {
            if (! dragging) {
                return
            }
            camera.phi = camera.phi + (mouse.x - prev_x) * mouse_speed
            camera.theta = camera.theta - (mouse.y - prev_y) * mouse_speed
            if (camera.theta > Math.PI) {
                camera.theta = Math.PI
            } else if (camera.theta < 0.0001) {
                // singularity at theta=0 appears to cause some issues with the lookAt function getting the correct orientation
                camera.theta = 0.0001
            }
            prev_x = mouse.x
            prev_y = mouse.y
            camera.updatePosition()
        }
        onWheel: {
            camera.radius = camera.radius - wheel.angleDelta.y*scroll_speed
            if (camera.radius < 400) {
                camera.radius = 400
            } else if (camera.radius > 3000) {
                camera.radius = 3000
            }
            camera.updatePosition()
        }

    }
}