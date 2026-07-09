import pytest
from fastapi.testclient import TestClient
from datetime import datetime
from main import app, bindings, lock
import time

client = TestClient(app)


def test_get_ip_without_proxy():
    """Тест 1: получение IP без прокси-заголовков"""
    response = client.get("/")
    print(response.text)
    assert response.status_code == 200
    assert "ip=\"" in response.text
    assert "hostname=\"not mentioned\"" in response.text


def test_get_ip_with_x_forwarded_for():
    """Тест 2: получение IP с заголовком X-Forwarded-For"""
    headers = {"X-Forwarded-For": "123.123.123.123"}
    response = client.get("/", headers=headers)
    print(response.text)
    assert response.status_code == 200
    assert 'ip="123.123.123.123"' in response.text


def test_get_ip_with_x_real_ip():
    """Тест 3: получение IP с заголовком X-Real-IP"""
    headers = {"X-Real-IP": "192.168.1.100"}
    response = client.get("/", headers=headers)
    assert response.status_code == 200
    assert 'ip="192.168.1.100"' in response.text


def test_save_and_retrieve_hostname():
    """Тест 4: сохранение и получение hostname"""
    ip = "10.0.0.1"
    headers = {"X-Real-IP": ip}
    
    # Сохраняем hostname
    response1 = client.get("/?hostname=TestPC&ttl=300", headers=headers)
    assert response1.status_code == 200
    assert 'hostname="TestPC"' in response1.text
    
    # Проверяем, что hostname сохранился между запросами
    response2 = client.get("/", headers=headers)
    assert response2.status_code == 200
    assert 'hostname="TestPC"' in response2.text
    
    # Очищаем
    with lock:
        if ip in bindings:
            del bindings[ip]


def test_hostname_expires_after_ttl():
    """Тест 5: hostname исчезает после истечения TTL"""
    ip = "10.0.0.2"
    headers = {"X-Real-IP": ip}
    
    # Сохраняем hostname с TTL = 1 секунда
    client.get("/?hostname=ExpiredPC&ttl=1", headers=headers)
    
    # Ждём истечения
    time.sleep(2)
    
    # Проверяем, что hostname больше не отображается
    response = client.get("/", headers=headers)
    assert response.status_code == 200
    assert 'hostname="not mentioned"' in response.text


def test_different_clients_have_different_hostnames():
    """Тест 6: разные IP-адреса имеют свои привязки"""
    # Клиент 1
    headers1 = {"X-Real-IP": "10.0.0.10"}
    response1 = client.get("/?hostname=ClientA&ttl=300", headers=headers1)
    assert 'hostname="ClientA"' in response1.text
    
    # Клиент 2
    headers2 = {"X-Real-IP": "10.0.0.20"}
    response2 = client.get("/?hostname=ClientB&ttl=300", headers=headers2)
    assert 'hostname="ClientB"' in response2.text
    
    # Проверяем, что клиент 1 всё ещё видит своё имя
    response3 = client.get("/", headers=headers1)
    assert 'hostname="ClientA"' in response3.text
    
    # Проверяем, что клиент 2 всё ещё видит своё имя
    response4 = client.get("/", headers=headers2)
    assert 'hostname="ClientB"' in response4.text
    
    # Очищаем
    with lock:
        for ip in ["10.0.0.10", "10.0.0.20"]:
            if ip in bindings:
                del bindings[ip]
