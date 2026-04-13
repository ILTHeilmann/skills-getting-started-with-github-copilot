import pytest
from fastapi import status


class TestGetActivities:
    """Tests for GET /activities endpoint."""

    def test_get_all_activities(self, client):
        """Should return all activities."""
        # Arrange - no setup needed, data is pre-populated
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert len(data) > 0

    def test_activity_structure(self, client):
        """Should return activities with correct structure."""
        # Arrange - no additional setup needed
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        activity = data["Chess Club"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)

    def test_activities_have_participants(self, client):
        """Should include participant list for each activity."""
        # Arrange - no additional setup needed
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        for activity_name, activity in data.items():
            assert isinstance(activity["participants"], list)
            # Participants should be emails
            for participant in activity["participants"]:
                assert "@" in participant


class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint."""

    def test_successful_signup(self, client, reset_activities):
        """Should successfully sign up a student."""
        # Arrange
        email = "newstudent@mergington.edu"
        activity_name = "Chess Club"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert email in data["message"]

    def test_signup_adds_participant(self, client, reset_activities):
        """Should add participant to the activity."""
        # Arrange
        email = "newstudent@mergington.edu"
        activity_name = "Chess Club"
        response = client.get("/activities")
        initial_count = len(response.json()[activity_name]["participants"])
        
        # Act
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        response = client.get("/activities")
        new_count = len(response.json()[activity_name]["participants"])
        assert new_count == initial_count + 1
        assert email in response.json()[activity_name]["participants"]

    def test_signup_nonexistent_activity(self, client, reset_activities):
        """Should return 404 for nonexistent activity."""
        # Arrange
        email = "student@mergington.edu"
        nonexistent_activity = "Nonexistent Activity"
        
        # Act
        response = client.post(
            f"/activities/{nonexistent_activity}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"].lower()

    def test_signup_duplicate_email(self, client, reset_activities):
        """Should reject duplicate signup."""
        # Arrange
        email = "michael@mergington.edu"  # Already signed up for Chess Club
        activity_name = "Chess Club"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already signed up" in response.json()["detail"].lower()

    def test_signup_different_activities(self, client, reset_activities):
        """Should allow same student to sign up for multiple activities."""
        # Arrange
        email = "student@mergington.edu"
        activity1 = "Chess Club"
        activity2 = "Programming Class"
        
        # Act
        response1 = client.post(
            f"/activities/{activity1}/signup",
            params={"email": email}
        )
        response2 = client.post(
            f"/activities/{activity2}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response1.status_code == status.HTTP_200_OK
        assert response2.status_code == status.HTTP_200_OK
        response = client.get("/activities")
        assert email in response.json()[activity1]["participants"]
        assert email in response.json()[activity2]["participants"]


class TestUnregister:
    """Tests for DELETE /activities/{activity_name}/participants endpoint."""

    def test_successful_unregister(self, client, reset_activities):
        """Should successfully unregister a participant."""
        # Arrange
        email = "michael@mergington.edu"  # Already in Chess Club
        activity_name = "Chess Club"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert email in data["message"]

    def test_unregister_removes_participant(self, client, reset_activities):
        """Should remove participant from activity."""
        # Arrange
        email = "michael@mergington.edu"
        activity_name = "Chess Club"
        response = client.get("/activities")
        initial_count = len(response.json()[activity_name]["participants"])
        
        # Act
        client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email}
        )
        
        # Assert
        response = client.get("/activities")
        new_count = len(response.json()[activity_name]["participants"])
        assert new_count == initial_count - 1
        assert email not in response.json()[activity_name]["participants"]

    def test_unregister_nonexistent_activity(self, client, reset_activities):
        """Should return 404 for nonexistent activity."""
        # Arrange
        email = "student@mergington.edu"
        nonexistent_activity = "Nonexistent Activity"
        
        # Act
        response = client.delete(
            f"/activities/{nonexistent_activity}/participants",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_unregister_nonexistent_participant(self, client, reset_activities):
        """Should return 404 if participant not found."""
        # Arrange
        email = "notregistered@mergington.edu"
        activity_name = "Chess Club"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"].lower()

    def test_re_signup_after_unregister(self, client, reset_activities):
        """Should allow re-signup after unregistering."""
        # Arrange
        email = "michael@mergington.edu"
        activity_name = "Chess Club"
        
        # Act - Unregister
        client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email}
        )
        
        # Act - Re-register
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        response = client.get("/activities")
        assert email in response.json()[activity_name]["participants"]


class TestRootRedirect:
    """Tests for GET / endpoint."""

    def test_root_redirects_to_index(self, client):
        """Should redirect root to static index.html."""
        # Arrange - no setup needed
        
        # Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code in (301, 302, 307, 308)
        assert "/static/index.html" in response.headers.get("location", "")
