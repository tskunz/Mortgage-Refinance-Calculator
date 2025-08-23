import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import seaborn as sns
import matplotlib.pyplot as plt

def load_titanic_data():
    """Load the Titanic dataset from seaborn"""
    titanic = sns.load_dataset('titanic')
    return titanic

def preprocess_data(df):
    """Preprocess the Titanic dataset"""
    df = df.copy()
    
    print("Dataset shape:", df.shape)
    print("\nMissing values:")
    print(df.isnull().sum())
    
    df['age'].fillna(df['age'].median(), inplace=True)
    df['embarked'].fillna(df['embarked'].mode()[0], inplace=True)
    df.drop(['deck'], axis=1, inplace=True)
    
    le = LabelEncoder()
    categorical_columns = ['sex', 'embarked', 'class', 'who', 'adult_male', 'alone']
    
    for col in categorical_columns:
        if col in df.columns:
            df[col] = le.fit_transform(df[col])
    
    features = ['pclass', 'sex', 'age', 'sibsp', 'parch', 'fare', 'embarked', 'adult_male', 'alone']
    X = df[features]
    y = df['survived']
    
    return X, y

def train_model(X, y):
    """Train logistic regression model"""
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    model = LogisticRegression(random_state=42)
    model.fit(X_train_scaled, y_train)
    
    return model, scaler, X_train_scaled, X_test_scaled, y_train, y_test

def evaluate_model(model, X_test_scaled, y_test):
    """Evaluate model performance"""
    y_pred = model.predict(X_test_scaled)
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"Accuracy: {accuracy:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, y_pred))
    
    return y_pred

def main():
    """Main function to run the Titanic classification"""
    print("=== Titanic Survival Classification with Logistic Regression ===\n")
    
    df = load_titanic_data()
    print("Dataset loaded successfully!")
    print(f"Dataset shape: {df.shape}")
    print("\nFirst few rows:")
    print(df.head())
    
    X, y = preprocess_data(df)
    print("\nData preprocessing completed!")
    
    model, scaler, X_train_scaled, X_test_scaled, y_train, y_test = train_model(X, y)
    print("\nModel training completed!")
    
    print("\n=== Model Evaluation ===")
    y_pred = evaluate_model(model, X_test_scaled, y_test)
    
    feature_importance = pd.DataFrame({
        'feature': X.columns,
        'coefficient': model.coef_[0]
    }).sort_values('coefficient', key=abs, ascending=False)
    
    print("\nFeature Importance (Coefficients):")
    print(feature_importance)

if __name__ == "__main__":
    main()