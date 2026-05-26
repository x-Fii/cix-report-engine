// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAnalytics } from "firebase/analytics";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyAkrJjjY4fKn8kOBVO2XZ61RYf--OefWow",
  authDomain: "service-form-496306.firebaseapp.com",
  projectId: "service-form-496306",
  storageBucket: "service-form-496306.firebasestorage.app",
  messagingSenderId: "604931191602",
  appId: "1:604931191602:web:99fbf4a3bf056c1e641d2b",
  measurementId: "G-N71HK4XF4Y"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);