"""Tests for the Activities API endpoints"""
import pytest
from urllib.parse import quote


class TestGetActivities:
    """Test suite for GET /activities endpoint"""

    def test_get_activities_success(self, client):
        """Test successfully retrieving all activities"""
        response = client.get("/activities")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify it's a dict (activity name -> details)
        assert isinstance(data, dict)
        assert len(data) > 0

    def test_get_activities_contains_expected_activities(self, client):
        """Test that all expected activities are returned"""
        response = client.get("/activities")
        data = response.json()
        
        expected_activities = [
            "Chess Club",
            "Programming Class",
            "Gym Class",
            "Basketball Team",
            "Tennis Club",
            "Art Studio",
            "Music Band",
            "Debate Club",
            "Science Olympiad",
        ]
        
        for activity_name in expected_activities:
            assert activity_name in data

    def test_get_activities_has_required_fields(self, client):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        data = response.json()
        
        required_fields = ["description", "schedule", "max_participants", "participants"]
        
        for activity_name, activity_details in data.items():
            for field in required_fields:
                assert field in activity_details, f"Activity '{activity_name}' missing field '{field}'"

    def test_get_activities_participants_is_list(self, client):
        """Test that participants field is always a list"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_details in data.items():
            assert isinstance(activity_details["participants"], list), \
                f"Activity '{activity_name}' participants should be a list"

    def test_get_activities_max_participants_is_positive_integer(self, client):
        """Test that max_participants is a positive integer"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_details in data.items():
            max_p = activity_details["max_participants"]
            assert isinstance(max_p, int) and max_p > 0, \
                f"Activity '{activity_name}' max_participants should be a positive integer"


class TestSignupActivity:
    """Test suite for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_success(self, fresh_app):
        """Test successful signup for an activity"""
        response = fresh_app.post(
            f"/activities/{quote('Chess Club')}/signup?email={quote('test@mergington.edu')}"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "test@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]

    def test_signup_adds_participant_to_list(self, fresh_app):
        """Test that signup actually adds the participant to the activity"""
        email = "newstudent@mergington.edu"
        fresh_app.post(f"/activities/{quote('Chess Club')}/signup?email={quote(email)}")
        
        response = fresh_app.get("/activities")
        data = response.json()
        
        assert email in data["Chess Club"]["participants"]

    def test_signup_duplicate_email_returns_400(self, fresh_app):
        """Test that signing up with same email twice returns 400"""
        email = "duplicate@mergington.edu"
        
        # First signup should succeed
        response1 = fresh_app.post(f"/activities/{quote('Chess Club')}/signup?email={quote(email)}")
        assert response1.status_code == 200
        
        # Second signup with same email should fail
        response2 = fresh_app.post(f"/activities/{quote('Chess Club')}/signup?email={quote(email)}")
        assert response2.status_code == 400
        
        data = response2.json()
        assert "already signed up" in data["detail"]

    def test_signup_nonexistent_activity_returns_404(self, fresh_app):
        """Test that signing up for non-existent activity returns 404"""
        response = fresh_app.post(
            f"/activities/{quote('NonExistent Activity')}/signup?email={quote('test@mergington.edu')}"
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_signup_multiple_different_emails_same_activity(self, fresh_app):
        """Test that multiple different students can sign up for same activity"""
        emails = ["student1@mergington.edu", "student2@mergington.edu", "student3@mergington.edu"]
        
        for email in emails:
            response = fresh_app.post(f"/activities/{quote('Programming Class')}/signup?email={quote(email)}")
            assert response.status_code == 200
        
        # Verify all are in the activity
        response = fresh_app.get("/activities")
        data = response.json()
        participants = data["Programming Class"]["participants"]
        
        for email in emails:
            assert email in participants

    def test_signup_same_email_different_activities(self, fresh_app):
        """Test that same student can sign up for multiple activities"""
        email = "versatile@mergington.edu"
        activities = ["Chess Club", "Programming Class", "Tennis Club"]
        
        for activity in activities:
            response = fresh_app.post(f"/activities/{quote(activity)}/signup?email={quote(email)}")
            assert response.status_code == 200
        
        # Verify student is in all activities
        response = fresh_app.get("/activities")
        data = response.json()
        
        for activity in activities:
            assert email in data[activity]["participants"]

    def test_signup_respects_max_participants(self, fresh_app):
        """Test that activities can reach max capacity"""
        activity = "Tennis Club"
        response = fresh_app.get("/activities")
        activity_data = response.json()[activity]
        max_p = activity_data["max_participants"]
        existing = len(activity_data["participants"])
        spots_available = max_p - existing
        
        # Sign up students until at capacity
        emails = [f"student{i}@mergington.edu" for i in range(spots_available)]
        
        for email in emails:
            response = fresh_app.post(f"/activities/{quote(activity)}/signup?email={quote(email)}")
            assert response.status_code == 200
        
        # Verify at capacity
        response = fresh_app.get("/activities")
        participants = response.json()[activity]["participants"]
        assert len(participants) == max_p

    def test_signup_special_characters_in_email(self, fresh_app):
        """Test signup with email containing special characters"""
        email = "test+tag@school.edu"
        response = fresh_app.post(f"/activities/{quote('Chess Club')}/signup?email={quote(email)}")
        
        assert response.status_code == 200
        
        # Verify in list
        response = fresh_app.get("/activities")
        assert email in response.json()["Chess Club"]["participants"]


class TestRemoveParticipant:
    """Test suite for DELETE /activities/{activity_name}/participants/{email} endpoint"""

    def test_remove_participant_success(self, fresh_app):
        """Test successfully removing a participant"""
        activity = "Chess Club"
        email = "michael@mergington.edu"  # Exists in initial data
        
        response = fresh_app.delete(
            f"/activities/{quote(activity)}/participants/{quote(email)}"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    def test_remove_participant_actually_removes(self, fresh_app):
        """Test that participant is actually removed from the list"""
        activity = "Chess Club"
        email = "michael@mergington.edu"
        
        # Verify they exist first
        response = fresh_app.get("/activities")
        assert email in response.json()[activity]["participants"]
        
        # Remove
        fresh_app.delete(f"/activities/{quote(activity)}/participants/{quote(email)}")
        
        # Verify they're gone
        response = fresh_app.get("/activities")
        assert email not in response.json()[activity]["participants"]

    def test_remove_nonexistent_activity_returns_404(self, fresh_app):
        """Test removing from non-existent activity returns 404"""
        response = fresh_app.delete(
            f"/activities/{quote('NonExistent Activity')}/participants/{quote('test@mergington.edu')}"
        )
        
        assert response.status_code == 404

    def test_remove_nonexistent_participant_returns_400(self, fresh_app):
        """Test removing non-existent participant returns 400"""
        response = fresh_app.delete(
            f"/activities/{quote('Chess Club')}/participants/{quote('nonexistent@mergington.edu')}"
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_remove_and_signup_again(self, fresh_app):
        """Test that student can re-signup after being removed"""
        activity = "Basketball Team"
        email = "rejoin@mergington.edu"
        
        # Sign up
        fresh_app.post(f"/activities/{quote(activity)}/signup?email={quote(email)}")
        
        response = fresh_app.get("/activities")
        assert email in response.json()[activity]["participants"]
        
        # Remove
        fresh_app.delete(f"/activities/{quote(activity)}/participants/{quote(email)}")
        
        response = fresh_app.get("/activities")
        assert email not in response.json()[activity]["participants"]
        
        # Re-signup
        response = fresh_app.post(f"/activities/{quote(activity)}/signup?email={quote(email)}")
        assert response.status_code == 200
        
        response = fresh_app.get("/activities")
        assert email in response.json()[activity]["participants"]

    def test_remove_multiple_participants(self, fresh_app):
        """Test removing multiple participants from same activity"""
        activity = "Programming Class"
        emails_to_remove = ["emma@mergington.edu", "sophia@mergington.edu"]
        
        # Remove them
        for email in emails_to_remove:
            response = fresh_app.delete(
                f"/activities/{quote(activity)}/participants/{quote(email)}"
            )
            assert response.status_code == 200
        
        # Verify all removed
        response = fresh_app.get("/activities")
        participants = response.json()[activity]["participants"]
        
        for email in emails_to_remove:
            assert email not in participants

    def test_remove_with_special_characters_in_email(self, fresh_app):
        """Test removing participant with special characters in email"""
        activity = "Art Studio"
        email = "special+tag@mergington.edu"
        
        # First sign them up
        fresh_app.post(f"/activities/{quote(activity)}/signup?email={quote(email)}")
        
        # Then remove
        response = fresh_app.delete(
            f"/activities/{quote(activity)}/participants/{quote(email)}"
        )
        
        assert response.status_code == 200
        
        # Verify removed
        response = fresh_app.get("/activities")
        assert email not in response.json()[activity]["participants"]


class TestIntegration:
    """Integration tests combining multiple operations"""

    def test_signup_then_get_reflects_change(self, fresh_app):
        """Test that GET /activities reflects signup immediately"""
        email = "integrated@mergington.edu"
        activity = "Debate Club"
        spots_before = fresh_app.get("/activities").json()[activity]["max_participants"] - \
                      len(fresh_app.get("/activities").json()[activity]["participants"])
        
        # Sign up
        fresh_app.post(f"/activities/{quote(activity)}/signup?email={quote(email)}")
        
        # Check availability decreased
        response = fresh_app.get("/activities")
        participants = response.json()[activity]["participants"]
        spots_after = response.json()[activity]["max_participants"] - len(participants)
        
        assert email in participants
        assert spots_after == spots_before - 1

    def test_signup_remove_signup_availability_correct(self, fresh_app):
        """Test availability is correct through signup -> remove -> signup cycle"""
        activity = "Science Olympiad"
        email = "cycle@mergington.edu"
        
        response1 = fresh_app.get("/activities")
        initial_count = len(response1.json()[activity]["participants"])
        
        # Sign up
        fresh_app.post(f"/activities/{quote(activity)}/signup?email={quote(email)}")
        response2 = fresh_app.get("/activities")
        after_signup = len(response2.json()[activity]["participants"])
        assert after_signup == initial_count + 1
        
        # Remove
        fresh_app.delete(f"/activities/{quote(activity)}/participants/{quote(email)}")
        response3 = fresh_app.get("/activities")
        after_remove = len(response3.json()[activity]["participants"])
        assert after_remove == initial_count
        
        # Sign up again
        fresh_app.post(f"/activities/{quote(activity)}/signup?email={quote(email)}")
        response4 = fresh_app.get("/activities")
        final_count = len(response4.json()[activity]["participants"])
        assert final_count == initial_count + 1
